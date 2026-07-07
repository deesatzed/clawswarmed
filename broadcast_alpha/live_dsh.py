import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .experiments import PANEL_TYPES, SEED_CONDITIONS, WORKSPACE_ARMS
from .ledger import Ledger
from .live_gate import (
    _build_openrouter_request,
    _decision,
    _effective_env,
    _provider_status,
    _sanitize_adapter_error,
    _sanitize_adapter_response,
    openrouter_chat_completion,
)
from .task_bank import CodebugTask, load_codebug_tasks, verify_patch


@dataclass(frozen=True)
class LiveDshResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _cells() -> list[dict]:
    return [
        {"panel_type": panel_type, "workspace_arm": arm, "seed_condition": seed_condition}
        for panel_type in PANEL_TYPES
        for arm in WORKSPACE_ARMS
        for seed_condition in SEED_CONDITIONS
    ]


def _task_request(
    api_key: str,
    model: str,
    seed: int,
    task: dict,
    cell: dict,
    task_index: int,
) -> dict:
    request = _build_openrouter_request(api_key=api_key, model=model, seed=seed)
    request["body"]["messages"] = [
        {
            "role": "system",
            "content": (
                "You are a bounded Broadcast-alpha pilot agent. Reply with one concise "
                "candidate rationale. Do not claim hidden-test access."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Task {task['id']} index {task_index}. Public prompt: {task['public_prompt']} "
                f"Panel={cell['panel_type']} arm={cell['workspace_arm']} seed_condition={cell['seed_condition']}. "
                "Preserve useful dissent before final consensus."
            ),
        },
    ]
    request["metadata"] = {
        "task_id": task["id"],
        "task_index": task_index,
        "panel_type": cell["panel_type"],
        "workspace_arm": cell["workspace_arm"],
        "seed_condition": cell["seed_condition"],
    }
    return request


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


def _extract_candidate_patch(response: dict) -> tuple[str | None, str]:
    content = _response_content(response).strip()
    if not content:
        return None, "empty_response"
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None, "missing_patch"
    if not isinstance(payload, dict) or not isinstance(payload.get("patch"), str) or not payload["patch"].strip():
        return None, "missing_patch"
    return payload["patch"].strip(), "parsed"


def _result_card(run_id: str, metrics: dict) -> str:
    if metrics["run_status"] == "blocked_no_live_execution":
        decision = "Live DSH pilot blocked."
        interpretation = "No adapter call was made. No secret values were recorded."
    else:
        decision = f"Live DSH pilot ran through {metrics['transport_label']} transport."
        interpretation = (
            "Fake transport verifies orchestration without external calls."
            if metrics["transport_label"] == "fake"
            else "Real provider transport executed; inspect costs and replay before using as evidence."
        )
    return f"""# Result Card: {run_id}

Run type: live DSH pilot
Prereg: {metrics['prereg_id']}

## Decision

{decision}

Run status: {metrics['run_status']}
Prereg file: {metrics['prereg_path']}
Prereg exists: {metrics['prereg_exists']}
Cell count: {metrics['cell_count']}
Planned task runs: {metrics['planned_task_runs']}
Task run count: {metrics['task_run_count']}
Adapter call count: {metrics['adapter_call_count']}
Candidate patches parsed: {metrics['candidate_patch_present_count']}
Hidden verifier pass count: {metrics['hidden_verifier_pass_count']}
Hidden verifier pass rate: {metrics['hidden_verifier_pass_rate']}
Live model run performed: {metrics['live_model_run_performed']}
Transport: {metrics['transport_label']}

## Interpretation

{interpretation}

This is a pilot rail. It does not replace the deterministic macro DSH result
and does not claim GLASSGATE_LIFT for live panels.

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_live_dsh(
    seed: int = 42,
    tasks_per_cell: int = 1,
    artifact_root: Path | None = None,
    env_file: Path | None = None,
    env: dict[str, str] | None = None,
    api_spend_authorized: bool = False,
    network_probe: bool = False,
    execute_live: bool = False,
    model: str | None = None,
    transport: Callable[[dict], dict] | None = None,
    transport_label: str = "real",
    prereg_path: Path | None = None,
) -> LiveDshResult:
    if tasks_per_cell < 1:
        raise ValueError("tasks_per_cell must be at least 1")

    artifact_root = artifact_root or Path("artifacts")
    run_id = f"live_dsh_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)
    prereg_path = prereg_path or Path("prereg/PREREG_LIVE-01.md")
    prereg_id = Path(prereg_path).stem
    prereg_exists = Path(prereg_path).exists()

    effective_env = _effective_env(env, env_file)
    model = model or effective_env.get("OPENROUTER_MODEL")
    provider_status = _provider_status(effective_env, api_spend_authorized, network_probe, execute_live, model)
    rail_status, reason_codes = _decision(provider_status)
    if rail_status == "ready_to_execute" and not prereg_exists:
        rail_status = "missing_preregistration"
        reason_codes = [*reason_codes, "missing_preregistration_file"]
    cells = _cells()
    planned_task_runs = len(cells) * tasks_per_cell
    task_bank: list[CodebugTask] = load_codebug_tasks()

    ledger = Ledger()
    ledger.append(
        "run_start",
        {
            "run_id": run_id,
            "seed": seed,
            "prereg_id": prereg_id,
            "prereg_path": str(prereg_path),
            "prereg_exists": prereg_exists,
            "run_type": "live_dsh_pilot",
            "cell_count": len(cells),
            "tasks_per_cell": tasks_per_cell,
        },
    )

    task_runs: list[dict] = []
    adapter_call_count = 0
    usage_total = 0
    adapter_errors: list[dict] = []
    live_model_run_performed = False
    candidate_patch_present_count = 0
    candidate_patch_parse_failure_count = 0
    hidden_verifier_pass_count = 0
    api_key = effective_env.get("OPENROUTER_API_KEY", "")

    if rail_status != "ready_to_execute":
        run_status = "blocked_no_live_execution"
        ledger.append(
            "live_dsh_blocked",
            {
                "rail_status": rail_status,
                "reason_codes": reason_codes,
                "planned_task_runs": planned_task_runs,
            },
        )
    else:
        run_status = "adapter_pilot_executed_fake_transport" if transport_label == "fake" else "live_dsh_executed"
        for cell in cells:
            for task_index in range(tasks_per_cell):
                task = task_bank[task_index % len(task_bank)]
                request = _task_request(api_key, model or "", seed, task.public_dict(), cell, task_index)
                try:
                    raw_response = (transport or openrouter_chat_completion)(request)
                    adapter_call_count += 1
                    live_model_run_performed = live_model_run_performed or transport_label != "fake"
                    adapter_response = _sanitize_adapter_response(raw_response)
                    usage_total += int(adapter_response.get("usage_total_tokens") or 0)
                    candidate_patch, parse_status = _extract_candidate_patch(raw_response)
                    if candidate_patch is None:
                        candidate_patch_parse_failure_count += 1
                        verification_payload = {
                            "passed": False,
                            "total": len(task.hidden_tests),
                            "failures": ({"parse_error": parse_status},),
                        }
                    else:
                        candidate_patch_present_count += 1
                        verification = verify_patch(task, candidate_patch)
                        verification_payload = verification.to_dict()
                        if verification.passed:
                            hidden_verifier_pass_count += 1
                    task_run = {
                        "task_id": task.id,
                        "task_index": task_index,
                        "panel_type": cell["panel_type"],
                        "workspace_arm": cell["workspace_arm"],
                        "seed_condition": cell["seed_condition"],
                        "adapter_response": adapter_response,
                        "candidate_patch": candidate_patch,
                        "candidate_patch_parse_status": parse_status,
                        "hidden_verifier_passed": verification_payload["passed"],
                        "hidden_verifier_total": verification_payload["total"],
                        "hidden_verifier_failures": verification_payload["failures"],
                        "transport_label": transport_label,
                    }
                    task_runs.append(task_run)
                    ledger.append("live_dsh_task_result", task_run)
                    ledger.append(
                        "live_dsh_verification",
                        {
                            "task_id": task.id,
                            "panel_type": cell["panel_type"],
                            "workspace_arm": cell["workspace_arm"],
                            "seed_condition": cell["seed_condition"],
                            "candidate_patch_parse_status": parse_status,
                            "hidden_verifier_passed": verification_payload["passed"],
                        },
                    )
                except Exception as exc:
                    adapter_call_count += 1
                    adapter_error = _sanitize_adapter_error(exc)
                    adapter_errors.append(adapter_error)
                    task_run = {
                        "task_id": task.id,
                        "task_index": task_index,
                        "panel_type": cell["panel_type"],
                        "workspace_arm": cell["workspace_arm"],
                        "seed_condition": cell["seed_condition"],
                        "candidate_patch": None,
                        "candidate_patch_parse_status": "adapter_error",
                        "hidden_verifier_passed": False,
                        "hidden_verifier_total": len(task.hidden_tests),
                        "hidden_verifier_failures": ({"adapter_error": adapter_error["error_type"]},),
                        "adapter_error": adapter_error,
                        "transport_label": transport_label,
                    }
                    task_runs.append(task_run)
                    ledger.append("live_dsh_task_error", task_run)
        if adapter_errors:
            run_status = "live_dsh_adapter_errors"
            reason_codes = ["adapter_errors_recorded"]
        else:
            reason_codes = [
                "adapter_calls_recorded",
                "fake_transport_no_external_api" if transport_label == "fake" else "live_provider_transport_executed",
            ]

    replay_contexts = {
        "agent_1": {
            "1": "Live DSH pilot: 24 panel/arm/seed-condition cells planned",
            "2": f"Live DSH pilot: adapter call count {adapter_call_count}",
            "3": "Live DSH pilot blocked: no live model execution"
            if adapter_call_count == 0
            else f"Live DSH pilot executed with {transport_label} transport",
        }
    }

    metrics = {
        "run_id": run_id,
        "run_status": run_status,
        "prereg_id": prereg_id,
        "prereg_path": str(prereg_path),
        "prereg_exists": prereg_exists,
        "seed": seed,
        "cell_count": len(cells),
        "tasks_per_cell": tasks_per_cell,
        "planned_task_runs": planned_task_runs,
        "task_run_count": len(task_runs),
        "adapter_call_count": adapter_call_count,
        "adapter_usage_total_tokens": usage_total,
        "candidate_patch_present_count": candidate_patch_present_count,
        "candidate_patch_parse_failure_count": candidate_patch_parse_failure_count,
        "hidden_verifier_pass_count": hidden_verifier_pass_count,
        "hidden_verifier_pass_rate": round(hidden_verifier_pass_count / len(task_runs), 6) if task_runs else 0.0,
        "provider": "openrouter",
        "openrouter_api_key_present": provider_status["required_env"]["OPENROUTER_API_KEY"]["present"],
        "model_configured": provider_status["model_configured"],
        "model_ref": provider_status["model_ref"],
        "api_spend_authorized": api_spend_authorized,
        "execute_live_requested": execute_live,
        "transport_label": transport_label,
        "live_model_run_performed": live_model_run_performed,
        "secret_values_recorded": False,
        "reason_codes": reason_codes,
        "task_runs_path": str(artifact_path / "task_runs.json"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "result_card_path": str(artifact_path / "result_card.md"),
    }
    ledger.append("metrics", metrics)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)

    _write_json(artifact_path / "task_runs.json", {"runs": task_runs})
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))

    return LiveDshResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
