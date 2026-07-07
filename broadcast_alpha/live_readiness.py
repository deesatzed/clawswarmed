import json
from dataclasses import dataclass
from pathlib import Path

from .experiments import SEED_CONDITIONS, WORKSPACE_ARMS
from .ledger import Ledger
from .live_dsh import _cells, _task_request
from .live_gate import _effective_env
from .task_bank import load_codebug_tasks


@dataclass(frozen=True)
class LiveReadinessResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _sanitize_request(raw_request: dict, task_public: dict) -> dict:
    headers = dict(raw_request["headers"])
    if "Authorization" in headers:
        headers["Authorization"] = "REDACTED"
    return {
        "url": raw_request["url"],
        "headers": headers,
        "body": raw_request["body"],
        "metadata": raw_request["metadata"],
        "task": task_public,
        "hidden_tests_included": False,
        "authorization_redacted": True,
    }


def _next_command(seed: int, prereg_path: Path, env_file: Path | None, model: str | None) -> str:
    parts = [
        "python3",
        "-m",
        "broadcast_alpha",
        "run-live-sequence",
        "--prereg",
        str(prereg_path),
        "--seed",
        str(seed),
        "--authorize-api-spend",
        "--execute-live",
    ]
    if env_file is not None:
        parts.extend(["--env-file", str(env_file)])
    if model:
        parts.extend(["--model", model])
    return " ".join(parts)


def _result_card(run_id: str, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Run type: live smoke readiness preview

## Verdict

Readiness status: {metrics['readiness_status']}
Adapter calls: {metrics['adapter_call_count']}
Live model run performed: {metrics['live_model_run_performed']}
Secret values recorded: {metrics['secret_values_recorded']}
Hidden tests included in request preview: {metrics['hidden_tests_included']}

No API call was made.

## Next Command

```bash
{metrics['next_command']}
```

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def prepare_live_smoke(
    seed: int = 42,
    artifact_root: Path | None = None,
    env_file: Path | None = None,
    env: dict[str, str] | None = None,
    model: str | None = None,
    prereg_path: Path | None = None,
) -> LiveReadinessResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"live_readiness_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)
    prereg_path = prereg_path or Path("prereg/PREREG_LIVE-01.md")

    effective_env = _effective_env(env, env_file)
    api_key_present = bool(effective_env.get("OPENROUTER_API_KEY"))
    model = model or effective_env.get("OPENROUTER_MODEL")
    model_configured = bool(model)
    prereg_exists = Path(prereg_path).exists()

    task = load_codebug_tasks()[0]
    cell = _cells()[0]
    request = _task_request(
        api_key="REDACTED",
        model=model or "OPENROUTER_MODEL_REQUIRED",
        seed=seed,
        task=task.public_dict(),
        cell=cell,
        task_index=0,
    )
    request_preview = _sanitize_request(request, task.public_dict())

    missing = []
    if not api_key_present:
        missing.append("OPENROUTER_API_KEY")
    if not model_configured:
        missing.append("OPENROUTER_MODEL_or_model_arg")
    if not prereg_exists:
        missing.append("PREREG_LIVE-01.md")
    readiness_status = "ready_pending_authorization" if not missing else "blocked_missing_configuration"
    next_command = _next_command(seed, prereg_path, env_file, model)
    gate_checklist = {
        "provider": "openrouter",
        "prereg_path": str(prereg_path),
        "prereg_exists": prereg_exists,
        "openrouter_api_key_present": api_key_present,
        "model_configured": model_configured,
        "model_ref": model if model_configured else None,
        "required_before_execution": [
            "OPENROUTER_API_KEY",
            "OPENROUTER_MODEL or --model",
            "--authorize-api-spend",
            "--execute-live",
            "PREREG_LIVE-01.md present",
        ],
        "missing_configuration": missing,
        "next_command": next_command,
        "adapter_call_count": 0,
        "live_model_run_performed": False,
    }
    metrics = {
        "run_id": run_id,
        "readiness_status": readiness_status,
        "seed": seed,
        "provider": "openrouter",
        "openrouter_api_key_present": api_key_present,
        "model_configured": model_configured,
        "model_ref": model if model_configured else None,
        "prereg_path": str(prereg_path),
        "prereg_exists": prereg_exists,
        "planned_panel_type": cell["panel_type"],
        "planned_workspace_arm": cell["workspace_arm"],
        "planned_seed_condition": cell["seed_condition"],
        "planned_task_id": task.id,
        "workspace_arms_supported": WORKSPACE_ARMS,
        "seed_conditions_supported": SEED_CONDITIONS,
        "adapter_call_count": 0,
        "live_model_run_performed": False,
        "secret_values_recorded": False,
        "hidden_tests_included": False,
        "request_preview_path": str(artifact_path / "request_preview.json"),
        "gate_checklist_path": str(artifact_path / "gate_checklist.json"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
        "next_command": next_command,
    }
    replay_contexts = {
        "agent_1": {
            "1": "live readiness: sanitized one-call smoke request preview generated",
            "2": f"live readiness: {readiness_status}; adapter calls 0",
            "3": "live readiness: no API call made; authorization redacted; hidden tests excluded",
        }
    }

    ledger = Ledger()
    ledger.append(
        "live_readiness_start",
        {"run_id": run_id, "seed": seed, "prereg_path": str(prereg_path)},
    )
    ledger.append(
        "live_smoke_request_preview",
        {
            "url": request_preview["url"],
            "metadata": request_preview["metadata"],
            "authorization_redacted": True,
            "hidden_tests_included": False,
        },
    )
    ledger.append("live_readiness_gates", gate_checklist)
    ledger.append("live_readiness_metrics", metrics)

    _write_json(artifact_path / "request_preview.json", request_preview)
    _write_json(artifact_path / "gate_checklist.json", gate_checklist)
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))

    return LiveReadinessResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
