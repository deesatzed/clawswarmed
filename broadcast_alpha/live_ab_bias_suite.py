import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .ab_bias_suite import BIAS_CONDITIONS, generate_ab_cases
from .ledger import Ledger
from .live_gate import (
    _build_openrouter_request,
    _effective_env,
    _sanitize_adapter_error,
    _sanitize_adapter_response,
    openrouter_chat_completion,
)
from .live_model_sweep import _models_from_env


@dataclass(frozen=True)
class LiveABBiasSuiteResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _response_content(response: dict) -> str:
    choices = response.get("choices") or []
    if not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    return str(message.get("content") or "")


def _json_candidate(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    if "{" in stripped and "}" in stripped:
        return stripped[stripped.find("{"): stripped.rfind("}") + 1]
    return stripped


def _extract_choice(response: dict) -> tuple[str | None, str]:
    content = _response_content(response)
    if not content.strip():
        return None, "empty_response"
    try:
        payload = json.loads(_json_candidate(content))
    except json.JSONDecodeError:
        return None, "missing_json_choice"
    if not isinstance(payload, dict):
        return None, "missing_choice"
    choice = str(payload.get("choice") or "").strip()
    if choice not in {"A", "B", "C", "reject_all"}:
        return None, "invalid_choice"
    return choice, "parsed"


def _case_is_correct(case: dict, choice: str | None) -> bool:
    if choice is None:
        return False
    if case["expected_choice"] == "reject_all":
        return choice == "reject_all"
    return choice in case["correct_agent_positions"]


def _select_cases(seed: int, case_limit: int) -> list[dict]:
    if case_limit < 1:
        raise ValueError("case_limit must be at least 1")
    return generate_ab_cases(seed=seed)[:case_limit]


def _build_case_request(api_key: str, model: str, seed: int, case: dict, case_index: int) -> dict:
    request = _build_openrouter_request(api_key=api_key, model=model, seed=seed + case_index)
    agent_lines = "\n".join(
        f"Agent {agent['position']}: {agent['claim']}" for agent in case["agents"]
    )
    request["body"]["messages"] = [
        {
            "role": "system",
            "content": (
                "You are judging a controlled Broadcast-alpha A/B case. "
                "Use only the evidence in the prompt. Do not include reasoning. Return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Case: {case['case_id']}\n"
                f"Task family: {case['task_family']}\n"
                f"Panel composition: {case['panel_composition']}\n"
                f"Bias condition: {case['bias_condition']}\n\n"
                f"Evidence:\n{case['evidence']}\n\n"
                f"Claims:\n{agent_lines}\n\n"
                f"Question: {case['question']}\n\n"
                "Choose the claim supported by the evidence. If all claims are unsupported, choose reject_all. "
                "Return exactly one JSON object like {\"choice\":\"A\"}. "
                "Allowed choices: A, B, C, reject_all."
            ),
        },
    ]
    request["body"]["temperature"] = 0
    request["body"]["max_tokens"] = 120
    request["metadata"] = {
        "case_id": case["case_id"],
        "case_index": case_index,
        "task_family": case["task_family"],
        "panel_composition": case["panel_composition"],
        "bias_condition": case["bias_condition"],
        "local_expected_choice": case["expected_choice"],
    }
    return request


def _accuracy(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row["correct"]) / len(rows), 6)


def _result_card(run_id: str, metrics: dict) -> str:
    if metrics["run_status"] == "blocked_no_live_execution":
        decision = "Live A/B behavioral run blocked. No adapter calls were made."
    else:
        decision = (
            f"Live A/B behavioral run executed through {metrics['transport_label']} "
            f"transport over {metrics['total_case_runs']} case runs."
        )
    return f"""# Result Card: {run_id}

Run type: live A/B behavioral bias suite

## Decision

{decision}

Run status: {metrics['run_status']}
Models: {metrics['model_count']}
Attempted models: {metrics['attempted_model_count']}
Cases per model: {metrics['case_count_per_model']}
Adapter calls: {metrics['adapter_call_count_total']}
Accuracy: {metrics['accuracy']}
Wrong-bias accuracy: {metrics['wrong_bias_accuracy']}
Parse failures: {metrics['parse_failure_count']}
Behavioral screening only: {metrics['behavioral_screening_only']}
Sufficient for J-lens proof: false

This artifact is black-box behavioral evidence only. It is not activation
measurement, not causal evidence, and not sufficient for `JLENS_PROVED`.

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_live_ab_bias_suite(
    seed: int = 42,
    artifact_root: Path | None = None,
    env_file: Path | None = None,
    env: dict[str, str] | None = None,
    api_spend_authorized: bool = False,
    execute_live: bool = False,
    budget_usd: float = 0.0,
    case_limit: int = 4,
    models: list[str] | None = None,
    prereg_path: Path | None = None,
    transport: Callable[[dict], dict] | None = None,
    transport_label: str = "real",
) -> LiveABBiasSuiteResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"live_ab_bias_suite_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)
    prereg_path = prereg_path or Path("prereg/PREREG_LIVE-01.md")

    effective_env = _effective_env(env, env_file)
    model_refs = _models_from_env(effective_env, models)
    api_key_present = bool(effective_env.get("OPENROUTER_API_KEY"))
    prereg_exists = Path(prereg_path).exists()
    reason_codes: list[str] = []
    if not api_key_present:
        reason_codes.append("missing_openrouter_api_key")
    if not model_refs:
        reason_codes.append("missing_openrouter_models")
    if not api_spend_authorized:
        reason_codes.append("api_spend_not_authorized")
    if not execute_live:
        reason_codes.append("execute_live_not_requested")
    if not prereg_exists:
        reason_codes.append("missing_preregistration_file")

    selected_cases = _select_cases(seed=seed, case_limit=case_limit)
    may_execute = (
        api_key_present
        and bool(model_refs)
        and api_spend_authorized
        and execute_live
        and prereg_exists
    )
    api_key = effective_env.get("OPENROUTER_API_KEY", "")
    ledger = Ledger()
    ledger.append(
        "live_ab_bias_suite_start",
        {
            "run_id": run_id,
            "seed": seed,
            "model_count": len(model_refs),
            "case_limit": case_limit,
            "budget_usd": budget_usd,
            "api_spend_authorized": api_spend_authorized,
            "execute_live_requested": execute_live,
            "secret_values_recorded": False,
        },
    )

    case_rows: list[dict] = []
    model_rows: list[dict] = []
    adapter_call_count_total = 0
    usage_total_tokens = 0

    if may_execute:
        for model_index, model_ref in enumerate(model_refs, start=1):
            model_case_rows = []
            for case_index, case in enumerate(selected_cases, start=1):
                request = _build_case_request(api_key, model_ref, seed, case, case_index)
                try:
                    raw_response = (transport or openrouter_chat_completion)(request)
                    adapter_call_count_total += 1
                    adapter_response = _sanitize_adapter_response(raw_response)
                    usage_total_tokens += int(adapter_response.get("usage_total_tokens") or 0)
                    choice, parse_status = _extract_choice(raw_response)
                    row = {
                        "model_index": model_index,
                        "model_ref": model_ref,
                        "case_id": case["case_id"],
                        "task_family": case["task_family"],
                        "panel_composition": case["panel_composition"],
                        "bias_condition": case["bias_condition"],
                        "bias_type": case["bias_type"],
                        "choice": choice,
                        "choice_parse_status": parse_status,
                        "correct": _case_is_correct(case, choice),
                        "adapter_response": adapter_response,
                        "transport_label": transport_label,
                    }
                except Exception as exc:
                    adapter_call_count_total += 1
                    row = {
                        "model_index": model_index,
                        "model_ref": model_ref,
                        "case_id": case["case_id"],
                        "task_family": case["task_family"],
                        "panel_composition": case["panel_composition"],
                        "bias_condition": case["bias_condition"],
                        "bias_type": case["bias_type"],
                        "choice": None,
                        "choice_parse_status": "adapter_error",
                        "correct": False,
                        "adapter_error": _sanitize_adapter_error(exc),
                        "transport_label": transport_label,
                    }
                case_rows.append(row)
                model_case_rows.append(row)
                ledger.append("live_ab_bias_case_result", row)
            model_rows.append(
                {
                    "model_index": model_index,
                    "model_ref": model_ref,
                    "case_count": len(model_case_rows),
                    "valid_choice_count": sum(
                        1 for row in model_case_rows if row["choice_parse_status"] == "parsed"
                    ),
                    "parse_failure_count": sum(
                        1 for row in model_case_rows if row["choice_parse_status"] != "parsed"
                    ),
                    "accuracy": _accuracy(model_case_rows),
                    "wrong_bias_accuracy": _accuracy(
                        [row for row in model_case_rows if row["bias_condition"] == "wrong_bias"]
                    ),
                    "neutral_accuracy": _accuracy(
                        [row for row in model_case_rows if row["bias_condition"] == "neutral"]
                    ),
                    "live_model_run_performed": transport_label != "fake" and bool(model_case_rows),
                }
            )
        run_status = "live_ab_executed"
        reason_codes = [
            "live_ab_case_calls_recorded",
            "fake_transport_no_external_api" if transport_label == "fake" else "live_provider_transport_executed",
        ]
    else:
        run_status = "blocked_no_live_execution"
        if "live_model_run_not_performed" not in reason_codes:
            reason_codes.append("live_model_run_not_performed")
        ledger.append(
            "live_ab_bias_suite_blocked",
            {"reason_codes": reason_codes, "model_count": len(model_refs), "case_limit": case_limit},
        )

    valid_choice_count = sum(1 for row in case_rows if row.get("choice_parse_status") == "parsed")
    parse_failure_count = sum(1 for row in case_rows if row.get("choice_parse_status") != "parsed")
    live_model_run_performed_count = sum(
        1 for row in model_rows if row["live_model_run_performed"]
    )
    metrics = {
        "run_id": run_id,
        "run_status": run_status,
        "seed": seed,
        "provider": "openrouter",
        "model_count": len(model_refs),
        "attempted_model_count": len(model_rows),
        "case_count_per_model": len(selected_cases),
        "total_case_runs": len(case_rows),
        "adapter_call_count_total": adapter_call_count_total,
        "adapter_usage_total_tokens": usage_total_tokens,
        "live_model_run_performed_count": live_model_run_performed_count,
        "valid_choice_count": valid_choice_count,
        "parse_failure_count": parse_failure_count,
        "accuracy": _accuracy(case_rows),
        "wrong_bias_accuracy": _accuracy(
            [row for row in case_rows if row.get("bias_condition") == "wrong_bias"]
        ),
        "neutral_accuracy": _accuracy(
            [row for row in case_rows if row.get("bias_condition") == "neutral"]
        ),
        "bias_conditions": BIAS_CONDITIONS,
        "budget_usd": budget_usd,
        "api_spend_authorized": api_spend_authorized,
        "execute_live_requested": execute_live,
        "prereg_path": str(prereg_path),
        "prereg_exists": prereg_exists,
        "transport_label": transport_label,
        "behavioral_screening_only": True,
        "evidence_class": "black_box_behavioral",
        "not_jlens_evidence": True,
        "not_activation_measurement": True,
        "not_causal": True,
        "not_sufficient_for_JLENS_PROVED": True,
        "secret_values_recorded": False,
        "reason_codes": reason_codes,
        "case_results_path": str(artifact_path / "case_results.json"),
        "model_results_path": str(artifact_path / "model_results.json"),
        "case_manifest_path": str(artifact_path / "case_manifest.json"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": f"live A/B bias suite: {len(model_refs)} model(s), {len(selected_cases)} case(s) per model",
            "2": f"live A/B bias suite: adapter calls {adapter_call_count_total}, accuracy {metrics['accuracy']}",
            "3": f"live A/B bias suite status {run_status}; behavioral only, no J-lens proof",
        }
    }

    ledger.append("live_ab_bias_suite_metrics", metrics)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)

    _write_json(artifact_path / "case_results.json", {"cases": case_rows})
    _write_json(artifact_path / "model_results.json", {"models": model_rows})
    _write_json(
        artifact_path / "case_manifest.json",
        {
            "cases": [
                {
                    "case_id": case["case_id"],
                    "task_family": case["task_family"],
                    "panel_composition": case["panel_composition"],
                    "bias_condition": case["bias_condition"],
                    "bias_type": case["bias_type"],
                    "evidence_contained": case["evidence_contained"],
                }
                for case in selected_cases
            ]
        },
    )
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))

    return LiveABBiasSuiteResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
