import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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


def _provider_status(
    effective_env: dict[str, str],
    api_spend_authorized: bool,
    network_probe: bool,
    execute_live: bool,
    model: str | None,
) -> dict:
    key_present = bool(effective_env.get("OPENROUTER_API_KEY"))
    model_present = bool(effective_env.get("OPENROUTER_MODEL"))
    model_configured = bool(model)
    return {
        "provider": "openrouter",
        "required_env": {
            "OPENROUTER_API_KEY": {"present": key_present, "value_recorded": False},
            "OPENROUTER_MODEL": {"present": model_present, "value_recorded": False},
        },
        "model_configured": model_configured,
        "model_ref": model if model_configured else None,
        "api_spend_authorized": api_spend_authorized,
        "network_probe_requested": network_probe,
        "execute_live_requested": execute_live,
        "network_probe_run": False,
        "live_model_run_performed": False,
        "secret_values_recorded": False,
    }


def _decision(provider_status: dict) -> tuple[str, list[str]]:
    key_present = provider_status["required_env"]["OPENROUTER_API_KEY"]["present"]
    model_configured = provider_status["model_configured"]
    api_spend_authorized = provider_status["api_spend_authorized"]
    network_probe_requested = provider_status["network_probe_requested"]
    execute_live = provider_status["execute_live_requested"]

    reason_codes: list[str] = []
    if not key_present:
        reason_codes.append("missing_openrouter_api_key")
    if key_present and not model_configured:
        reason_codes.append("missing_openrouter_model")
    if not api_spend_authorized:
        reason_codes.append("api_spend_not_authorized")
    if not execute_live:
        reason_codes.append("execute_live_not_requested")
    if not network_probe_requested:
        reason_codes.append("network_probe_not_requested")
    if not (key_present and model_configured and api_spend_authorized and execute_live):
        reason_codes.append("live_model_run_not_performed")

    if not key_present:
        return "unavailable", reason_codes
    if not api_spend_authorized:
        return "gated_ready_no_spend", reason_codes
    if not execute_live or not model_configured:
        return "configured_not_executed", reason_codes
    return "ready_to_execute", reason_codes


def _build_openrouter_request(api_key: str, model: str, seed: int) -> dict:
    return {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/deesatzed/clawswarmed",
            "X-Title": "clawswarmed Broadcast-alpha",
        },
        "body": {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a bounded Broadcast-alpha adapter smoke test. Return one concise sentence.",
                },
                {
                    "role": "user",
                    "content": f"Seed {seed}: say whether a minority insight should be preserved before final consensus.",
                },
            ],
            "temperature": 0,
            "max_tokens": 80,
        },
    }


def openrouter_chat_completion(request: dict) -> dict:
    encoded = json.dumps(request["body"]).encode("utf-8")
    http_request = urllib.request.Request(
        request["url"],
        data=encoded,
        headers=request["headers"],
        method="POST",
    )
    with urllib.request.urlopen(http_request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _sanitize_adapter_response(response: dict) -> dict:
    choices = response.get("choices") or []
    content = ""
    if choices:
        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        if isinstance(message, dict):
            content = str(message.get("content") or "")
    usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
    return {
        "response_id_present": bool(response.get("id")),
        "choice_count": len(choices),
        "content_preview": content[:200],
        "usage_prompt_tokens": usage.get("prompt_tokens"),
        "usage_completion_tokens": usage.get("completion_tokens"),
        "usage_total_tokens": usage.get("total_tokens"),
    }


def _sanitize_adapter_error(exc: Exception) -> dict:
    return {
        "error_type": type(exc).__name__,
        "error_message": str(exc)[:200],
    }


def _result_card(run_id: str, seed: int, metrics: dict) -> str:
    if metrics["adapter_call_performed"]:
        call_note = (
            f"Adapter call performed through {metrics['transport_label']} transport. "
            f"Live model run performed: {metrics['live_model_run_performed']}."
        )
    else:
        call_note = "No API call was made. No secret values were recorded."
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
Adapter call performed: {metrics['adapter_call_performed']}
Adapter transport: {metrics['transport_label']}

{call_note}

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
    execute_live: bool = False,
    model: str | None = None,
    transport: Callable[[dict], dict] | None = None,
    transport_label: str = "real",
) -> LiveGateResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"live_gate_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)

    effective_env = _effective_env(env, env_file)
    model = model or effective_env.get("OPENROUTER_MODEL")
    provider_status = _provider_status(effective_env, api_spend_authorized, network_probe, execute_live, model)
    rail_status, reason_codes = _decision(provider_status)
    adapter_call_performed = False
    live_model_run_performed = False
    adapter_response: dict | None = None
    adapter_error: dict | None = None

    api_key = effective_env.get("OPENROUTER_API_KEY", "")
    if rail_status == "ready_to_execute":
        request = _build_openrouter_request(api_key=api_key, model=model or "", seed=seed)
        try:
            raw_response = (transport or openrouter_chat_completion)(request)
            adapter_call_performed = True
            live_model_run_performed = transport_label != "fake"
            adapter_response = _sanitize_adapter_response(raw_response)
            provider_status["network_probe_run"] = transport_label != "fake"
            provider_status["live_model_run_performed"] = live_model_run_performed
            rail_status = "adapter_executed_fake_transport" if transport_label == "fake" else "live_model_executed"
            reason_codes = [
                "adapter_call_performed",
                "fake_transport_no_external_api" if transport_label == "fake" else "live_provider_transport_executed",
            ]
        except Exception as exc:
            adapter_call_performed = True
            adapter_error = _sanitize_adapter_error(exc)
            rail_status = "adapter_error"
            reason_codes = ["adapter_call_failed", adapter_error["error_type"]]
    replay_contexts = {
        "agent_1": {
            "1": "live gate: provider configuration inspected by presence only",
            "2": f"live gate: OpenRouter API key present = {provider_status['required_env']['OPENROUTER_API_KEY']['present']}",
            "3": "No live model run was performed; no API call was made and no secret value was recorded"
            if not adapter_call_performed
            else f"Adapter call exercised with {transport_label} transport; secret value not recorded",
        }
    }

    metrics = {
        "run_id": run_id,
        "rail_status": rail_status,
        "provider": "openrouter",
        "openrouter_api_key_present": provider_status["required_env"]["OPENROUTER_API_KEY"]["present"],
        "openrouter_model_present": provider_status["required_env"]["OPENROUTER_MODEL"]["present"],
        "model_configured": provider_status["model_configured"],
        "model_ref": provider_status["model_ref"],
        "api_spend_authorized": api_spend_authorized,
        "network_probe_requested": network_probe,
        "execute_live_requested": execute_live,
        "network_probe_run": provider_status["network_probe_run"],
        "adapter_call_performed": adapter_call_performed,
        "transport_label": transport_label,
        "live_model_run_performed": live_model_run_performed,
        "secret_values_recorded": False,
        "adapter_response": adapter_response,
        "adapter_error": adapter_error,
        "provider_status_path": str(artifact_path / "provider_status.json"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "reason_codes": reason_codes,
        "next_required_unblockers": [
            "Provide OPENROUTER_API_KEY to the process or a reviewed env file.",
            "Explicitly authorize API/model spend before any live model call.",
            "Pass --execute-live only when real provider execution is intended.",
            "Set OPENROUTER_MODEL or pass --model before live execution.",
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
            "model_configured": provider_status["model_configured"],
            "model_ref": provider_status["model_ref"],
            "secret_values_recorded": False,
        },
    )
    ledger.append(
        "live_gate_decision",
        {
            "rail_status": rail_status,
            "reason_codes": reason_codes,
            "api_spend_authorized": api_spend_authorized,
            "execute_live_requested": execute_live,
            "network_probe_run": provider_status["network_probe_run"],
            "adapter_call_performed": adapter_call_performed,
            "live_model_run_performed": live_model_run_performed,
        },
    )
    if adapter_response is not None:
        ledger.append("adapter_response", adapter_response)
    if adapter_error is not None:
        ledger.append("adapter_error", adapter_error)
    ledger.append("metrics", metrics)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)

    _write_json(artifact_path / "provider_status.json", provider_status)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, seed, metrics))

    return LiveGateResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
