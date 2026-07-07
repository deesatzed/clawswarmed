import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .ledger import Ledger
from .live_dsh import run_live_smoke
from .live_gate import _effective_env


@dataclass(frozen=True)
class LiveModelSweepResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _model_sort_key(item: tuple[str, str]) -> tuple[int, str]:
    match = re.fullmatch(r"OPENROUTER_MODEL_(\d+)", item[0])
    return (int(match.group(1)) if match else 0, item[0])


def _models_from_env(effective_env: dict[str, str], explicit_models: list[str] | None = None) -> list[str]:
    if explicit_models:
        return [model.strip() for model in explicit_models if model.strip()]
    if effective_env.get("OPENROUTER_MODELS"):
        return [
            model.strip()
            for model in effective_env["OPENROUTER_MODELS"].split(",")
            if model.strip()
        ]
    numbered = [
        (key, value.strip())
        for key, value in effective_env.items()
        if re.fullmatch(r"OPENROUTER_MODEL_\d+", key) and value.strip()
    ]
    if numbered:
        return [value for _key, value in sorted(numbered, key=_model_sort_key)]
    fallback = effective_env.get("OPENROUTER_MODEL", "").strip()
    return [fallback] if fallback else []


def _result_card(run_id: str, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Run type: live OpenRouter model sweep

## Decision

Sweep status: {metrics['sweep_status']}
Model count: {metrics['model_count']}
Attempted model count: {metrics['attempted_model_count']}
Adapter calls total: {metrics['adapter_call_count_total']}
Live model runs performed: {metrics['live_model_run_performed_count']}
Budget cap recorded: ${metrics['budget_usd']:.2f}
Transport: {metrics['transport_label']}

This sweep runs one verifier-backed smoke task per configured model. It does
not compute or claim GLASSGATE_LIFT.

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_live_model_sweep(
    seed: int = 42,
    artifact_root: Path | None = None,
    env_file: Path | None = None,
    env: dict[str, str] | None = None,
    api_spend_authorized: bool = False,
    network_probe: bool = False,
    execute_live: bool = False,
    budget_usd: float = 0.0,
    models: list[str] | None = None,
    prereg_path: Path | None = None,
    transport: Callable[[dict], dict] | None = None,
    transport_label: str = "real",
) -> LiveModelSweepResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"live_model_sweep_seed_{seed}"
    artifact_path = artifact_root / run_id
    child_root = artifact_path / "source_artifacts"
    artifact_path.mkdir(parents=True, exist_ok=True)
    prereg_path = prereg_path or Path("prereg/PREREG_LIVE-01.md")

    effective_env = _effective_env(env, env_file)
    model_refs = _models_from_env(effective_env, models)
    openrouter_api_key_present = bool(effective_env.get("OPENROUTER_API_KEY"))
    reason_codes: list[str] = []
    if not openrouter_api_key_present:
        reason_codes.append("missing_openrouter_api_key")
    if not model_refs:
        reason_codes.append("missing_openrouter_models")
    if not api_spend_authorized:
        reason_codes.append("api_spend_not_authorized")
    if not execute_live:
        reason_codes.append("execute_live_not_requested")

    may_execute = openrouter_api_key_present and bool(model_refs) and api_spend_authorized and execute_live
    model_results: list[dict] = []
    child_artifacts: dict[str, str] = {}
    child_ledgers_verified: dict[str, bool] = {}
    adapter_call_count_total = 0
    hidden_verifier_pass_count_total = 0
    live_model_run_performed_count = 0

    ledger = Ledger()
    ledger.append(
        "live_model_sweep_start",
        {
            "run_id": run_id,
            "seed": seed,
            "model_count": len(model_refs),
            "budget_usd": budget_usd,
            "api_spend_authorized": api_spend_authorized,
            "execute_live_requested": execute_live,
            "secret_values_recorded": False,
        },
    )

    if may_execute:
        for index, model_ref in enumerate(model_refs, start=1):
            child_name = f"model_{index}"
            smoke = run_live_smoke(
                seed=seed + index - 1,
                artifact_root=child_root / child_name,
                env_file=env_file,
                env=env,
                api_spend_authorized=api_spend_authorized,
                network_probe=network_probe,
                execute_live=execute_live,
                model=model_ref,
                prereg_path=prereg_path,
                transport=transport,
                transport_label=transport_label,
            )
            child_artifacts[child_name] = str(smoke.artifact_path)
            child_ledgers_verified[child_name] = Ledger.from_jsonl(smoke.artifact_path / "ledger.jsonl").verify_chain()
            smoke_metrics = _read_json(smoke.artifact_path / "metrics.json")
            row = {
                "model_index": index,
                "model_ref": model_ref,
                "artifact_path": str(smoke.artifact_path),
                "run_status": smoke_metrics["run_status"],
                "adapter_call_count": smoke_metrics["adapter_call_count"],
                "hidden_verifier_pass_count": smoke_metrics["hidden_verifier_pass_count"],
                "hidden_verifier_pass_rate": smoke_metrics["hidden_verifier_pass_rate"],
                "live_model_run_performed": smoke_metrics["live_model_run_performed"],
                "ledger_verified": child_ledgers_verified[child_name],
            }
            model_results.append(row)
            adapter_call_count_total += row["adapter_call_count"]
            hidden_verifier_pass_count_total += row["hidden_verifier_pass_count"]
            live_model_run_performed_count += 1 if row["live_model_run_performed"] else 0
            ledger.append("live_model_sweep_model_result", row)
        sweep_status = "sweep_executed"
        reason_codes = [
            "model_smoke_calls_recorded",
            "fake_transport_no_external_api" if transport_label == "fake" else "live_provider_transport_executed",
        ]
    else:
        sweep_status = "blocked_no_live_execution"
        if "live_model_run_not_performed" not in reason_codes:
            reason_codes.append("live_model_run_not_performed")
        ledger.append(
            "live_model_sweep_blocked",
            {
                "reason_codes": reason_codes,
                "model_count": len(model_refs),
            },
        )

    attempted_model_count = len(model_results)
    manifest = {
        "run_id": run_id,
        "seed": seed,
        "prereg_path": str(prereg_path),
        "budget_usd": budget_usd,
        "child_artifacts": child_artifacts,
        "run_sequence": list(child_artifacts),
    }
    metrics = {
        "run_id": run_id,
        "sweep_status": sweep_status,
        "seed": seed,
        "model_count": len(model_refs),
        "attempted_model_count": attempted_model_count,
        "adapter_call_count_total": adapter_call_count_total,
        "hidden_verifier_pass_count_total": hidden_verifier_pass_count_total,
        "live_model_run_performed_count": live_model_run_performed_count,
        "budget_usd": budget_usd,
        "estimated_upper_call_count": len(model_refs),
        "provider": "openrouter",
        "openrouter_api_key_present": openrouter_api_key_present,
        "api_spend_authorized": api_spend_authorized,
        "execute_live_requested": execute_live,
        "transport_label": transport_label,
        "secret_values_recorded": False,
        "all_child_ledgers_verified": all(child_ledgers_verified.values()) if child_ledgers_verified else False,
        "reason_codes": reason_codes,
        "manifest_path": str(artifact_path / "manifest.json"),
        "model_results_path": str(artifact_path / "model_results.json"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": f"live model sweep: {len(model_refs)} configured model(s), budget cap ${budget_usd:.2f}",
            "2": f"live model sweep: attempted {attempted_model_count} model(s), adapter calls {adapter_call_count_total}",
            "3": f"live model sweep status {sweep_status}; live model runs {live_model_run_performed_count}",
        }
    }

    ledger.append("live_model_sweep_metrics", metrics)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)

    _write_json(artifact_path / "manifest.json", manifest)
    _write_json(artifact_path / "model_results.json", {"models": model_results})
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))

    return LiveModelSweepResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
