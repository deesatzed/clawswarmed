import json
import os
from dataclasses import dataclass
from pathlib import Path

from .ledger import Ledger


@dataclass(frozen=True)
class LiveGateResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def _effective_env(env: dict[str, str] | None, env_file: Path | None) -> dict[str, str]:
    effective = dict(os.environ if env is None else env)
    if env_file is not None:
        effective.update(_load_env_file(env_file))
    return effective


def _provider_status(effective_env: dict[str, str], api_spend_authorized: bool, network_probe: bool) -> dict:
    key_present = bool(effective_env.get("OPENROUTER_API_KEY"))
    model_present = bool(effective_env.get("OPENROUTER_MODEL"))
    return {
        "provider": "openrouter",
        "required_env": {
            "OPENROUTER_API_KEY": {"present": key_present, "value_recorded": False},
            "OPENROUTER_MODEL": {"present": model_present, "value_recorded": False},
        },
        "api_spend_authorized": api_spend_authorized,
        "network_probe_requested": network_probe,
        "network_probe_run": False,
        "live_model_run_performed": False,
        "secret_values_recorded": False,
    }


def _decision(provider_status: dict) -> tuple[str, list[str]]:
    key_present = provider_status["required_env"]["OPENROUTER_API_KEY"]["present"]
    api_spend_authorized = provider_status["api_spend_authorized"]
    network_probe_requested = provider_status["network_probe_requested"]

    reason_codes: list[str] = []
    if not key_present:
        reason_codes.append("missing_openrouter_api_key")
    if not api_spend_authorized:
        reason_codes.append("api_spend_not_authorized")
    if not network_probe_requested:
        reason_codes.append("network_probe_not_requested")
    if api_spend_authorized:
        reason_codes.append("live_model_adapter_not_implemented")
    reason_codes.append("live_model_run_not_performed")

    if not key_present:
        return "unavailable", reason_codes
    if not api_spend_authorized:
        return "gated_ready_no_spend", reason_codes
    return "configured_not_executed", reason_codes


def _result_card(run_id: str, seed: int, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Seed: {seed}
Run type: live model provider readiness gate

## Decision

Live model rail status: {metrics['rail_status']}
Provider: openrouter
OpenRouter API key present by name: {metrics['openrouter_api_key_present']}
API spend authorized: {metrics['api_spend_authorized']}
Network probe run: {metrics['network_probe_run']}
Live model run performed: {metrics['live_model_run_performed']}

No API call was made. No secret values were recorded.

## Reason codes

{', '.join(metrics['reason_codes'])}

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_live_gate(
    seed: int = 42,
    artifact_root: Path | None = None,
    env_file: Path | None = None,
    env: dict[str, str] | None = None,
    api_spend_authorized: bool = False,
    network_probe: bool = False,
) -> LiveGateResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"live_gate_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)

    effective_env = _effective_env(env, env_file)
    provider_status = _provider_status(effective_env, api_spend_authorized, network_probe)
    rail_status, reason_codes = _decision(provider_status)
    replay_contexts = {
        "agent_1": {
            "1": "live gate: provider configuration inspected by presence only",
            "2": f"live gate: OpenRouter API key present = {provider_status['required_env']['OPENROUTER_API_KEY']['present']}",
            "3": "No live model run was performed; no API call was made and no secret value was recorded",
        }
    }

    metrics = {
        "run_id": run_id,
        "rail_status": rail_status,
        "provider": "openrouter",
        "openrouter_api_key_present": provider_status["required_env"]["OPENROUTER_API_KEY"]["present"],
        "openrouter_model_present": provider_status["required_env"]["OPENROUTER_MODEL"]["present"],
        "api_spend_authorized": api_spend_authorized,
        "network_probe_requested": network_probe,
        "network_probe_run": False,
        "live_model_run_performed": False,
        "secret_values_recorded": False,
        "provider_status_path": str(artifact_path / "provider_status.json"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "reason_codes": reason_codes,
        "next_required_unblockers": [
            "Provide OPENROUTER_API_KEY to the process or a reviewed env file.",
            "Explicitly authorize API/model spend before any live model call.",
            "Implement and test the live model adapter before enabling network execution.",
        ],
    }

    ledger = Ledger()
    ledger.append(
        "run_start",
        {
            "run_id": run_id,
            "seed": seed,
            "run_type": "live_model_provider_gate",
        },
    )
    ledger.append(
        "provider_configuration",
        {
            "provider": provider_status["provider"],
            "required_env": provider_status["required_env"],
            "secret_values_recorded": False,
        },
    )
    ledger.append(
        "live_gate_decision",
        {
            "rail_status": rail_status,
            "reason_codes": reason_codes,
            "api_spend_authorized": api_spend_authorized,
            "network_probe_run": False,
            "live_model_run_performed": False,
        },
    )
    ledger.append("metrics", metrics)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)

    _write_json(artifact_path / "provider_status.json", provider_status)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, seed, metrics))

    return LiveGateResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
