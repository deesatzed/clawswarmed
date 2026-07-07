import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .ledger import Ledger
from .live_dsh import run_live_dsh, run_live_smoke
from .live_gate import run_live_gate


@dataclass(frozen=True)
class LiveSequenceResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _verify_ledger(artifact_path: Path) -> bool:
    return Ledger.from_jsonl(artifact_path / "ledger.jsonl").verify_chain()


def _result_card(run_id: str, metrics: dict, manifest: dict) -> str:
    child_rows = "\n".join(
        f"| {name} | {path} | {metrics['child_ledgers_verified'][name]} |"
        for name, path in manifest["child_artifacts"].items()
    )
    status_note = (
        "The sequence is blocked before smoke; no adapter call was made."
        if metrics["sequence_status"] == "blocked_before_smoke"
        else f"The sequence reached status `{metrics['sequence_status']}`."
    )
    return f"""# Result Card: {run_id}

Run type: live provider execution sequence

## Decision

Sequence status: {metrics['sequence_status']}
Adapter calls total: {metrics['adapter_call_count_total']}
Smoke status: {metrics['smoke_run_status']}
Smoke hidden verifier pass count: {metrics['smoke_hidden_verifier_pass_count']}
Pilot requested: {metrics['include_dsh_pilot']}
Pilot promoted: {metrics['pilot_promoted']}
Pilot status: {metrics['pilot_run_status']}

{status_note}

This sequence does not compute or claim GLASSGATE_LIFT.

## Child artifacts

| Artifact | Path | Ledger verified |
|---|---|---:|
{child_rows}

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def _sequence_status(
    smoke_metrics: dict,
    include_dsh_pilot: bool,
    pilot_promoted: bool,
    pilot_metrics: dict | None,
) -> str:
    if smoke_metrics["adapter_call_count"] == 0:
        return "blocked_before_smoke"
    smoke_passed = smoke_metrics["hidden_verifier_pass_count"] > 0
    if not smoke_passed:
        return "smoke_failed_pilot_not_promoted" if include_dsh_pilot else "smoke_failed_pilot_not_requested"
    if not include_dsh_pilot:
        return "smoke_passed_pilot_not_requested"
    if pilot_promoted and pilot_metrics is not None:
        return "pilot_executed_after_smoke_pass"
    return "smoke_passed_pilot_not_promoted"


def run_live_sequence(
    seed: int = 42,
    artifact_root: Path | None = None,
    env_file: Path | None = None,
    env: dict[str, str] | None = None,
    api_spend_authorized: bool = False,
    network_probe: bool = False,
    execute_live: bool = False,
    model: str | None = None,
    include_dsh_pilot: bool = False,
    prereg_path: Path | None = None,
    transport: Callable[[dict], dict] | None = None,
    transport_label: str = "real",
) -> LiveSequenceResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"live_sequence_seed_{seed}"
    artifact_path = artifact_root / run_id
    child_root = artifact_path / "source_artifacts"
    artifact_path.mkdir(parents=True, exist_ok=True)

    prereg_path = prereg_path or Path("prereg/PREREG_LIVE-01.md")

    # The readiness gate records provider configuration without making an
    # adapter call. Spend, if explicitly authorized, starts with smoke.
    live_gate = run_live_gate(
        seed=seed,
        artifact_root=child_root,
        env_file=env_file,
        env=env,
        api_spend_authorized=api_spend_authorized,
        network_probe=network_probe,
        execute_live=False,
        model=model,
    )
    live_smoke = run_live_smoke(
        seed=seed,
        artifact_root=child_root,
        env_file=env_file,
        env=env,
        api_spend_authorized=api_spend_authorized,
        network_probe=network_probe,
        execute_live=execute_live,
        model=model,
        transport=transport,
        transport_label=transport_label,
        prereg_path=prereg_path,
    )

    smoke_metrics = _read_json(live_smoke.artifact_path / "metrics.json")
    smoke_passed = smoke_metrics["hidden_verifier_pass_count"] > 0
    pilot_promoted = bool(include_dsh_pilot and smoke_passed)
    live_dsh = None
    pilot_metrics = None
    if pilot_promoted:
        live_dsh = run_live_dsh(
            seed=seed,
            tasks_per_cell=1,
            artifact_root=child_root,
            env_file=env_file,
            env=env,
            api_spend_authorized=api_spend_authorized,
            network_probe=network_probe,
            execute_live=execute_live,
            model=model,
            transport=transport,
            transport_label=transport_label,
            prereg_path=prereg_path,
        )
        pilot_metrics = _read_json(live_dsh.artifact_path / "metrics.json")

    child_artifacts = {
        "live_model_gate": str(live_gate.artifact_path),
        "live_smoke": str(live_smoke.artifact_path),
    }
    child_paths = {
        "live_model_gate": live_gate.artifact_path,
        "live_smoke": live_smoke.artifact_path,
    }
    if live_dsh is not None:
        child_artifacts["live_dsh_pilot"] = str(live_dsh.artifact_path)
        child_paths["live_dsh_pilot"] = live_dsh.artifact_path

    child_ledgers_verified = {
        name: _verify_ledger(path)
        for name, path in child_paths.items()
    }
    gate_metrics = _read_json(live_gate.artifact_path / "metrics.json")
    pilot_run_status = pilot_metrics["run_status"] if pilot_metrics is not None else "not_requested"
    pilot_adapter_call_count = pilot_metrics["adapter_call_count"] if pilot_metrics is not None else 0
    pilot_hidden_verifier_pass_count = pilot_metrics["hidden_verifier_pass_count"] if pilot_metrics is not None else 0
    sequence_status = _sequence_status(smoke_metrics, include_dsh_pilot, pilot_promoted, pilot_metrics)
    adapter_call_count_total = smoke_metrics["adapter_call_count"] + pilot_adapter_call_count

    manifest = {
        "run_id": run_id,
        "seed": seed,
        "prereg_path": str(prereg_path),
        "include_dsh_pilot": include_dsh_pilot,
        "child_artifacts": child_artifacts,
        "run_sequence": list(child_artifacts),
    }
    metrics = {
        "run_id": run_id,
        "sequence_status": sequence_status,
        "seed": seed,
        "prereg_path": str(prereg_path),
        "prereg_exists": Path(prereg_path).exists(),
        "include_dsh_pilot": include_dsh_pilot,
        "pilot_promoted": pilot_promoted,
        "adapter_call_count_total": adapter_call_count_total,
        "live_model_gate_status": gate_metrics["rail_status"],
        "live_model_gate_adapter_call_performed": gate_metrics["adapter_call_performed"],
        "smoke_run_status": smoke_metrics["run_status"],
        "smoke_adapter_call_count": smoke_metrics["adapter_call_count"],
        "smoke_candidate_patch_present_count": smoke_metrics["candidate_patch_present_count"],
        "smoke_hidden_verifier_pass_count": smoke_metrics["hidden_verifier_pass_count"],
        "smoke_hidden_verifier_pass_rate": smoke_metrics["hidden_verifier_pass_rate"],
        "smoke_model_run_performed": smoke_metrics["live_model_run_performed"],
        "pilot_run_status": pilot_run_status,
        "pilot_adapter_call_count": pilot_adapter_call_count,
        "pilot_hidden_verifier_pass_count": pilot_hidden_verifier_pass_count,
        "child_ledgers_verified": child_ledgers_verified,
        "all_child_ledgers_verified": all(child_ledgers_verified.values()),
        "manifest_path": str(artifact_path / "manifest.json"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": "live sequence: provider readiness gate and bounded smoke path prepared",
            "2": f"live sequence: smoke status {smoke_metrics['run_status']} with {smoke_metrics['adapter_call_count']} adapter call(s)",
            "3": f"live sequence blocked before smoke: {smoke_metrics['reason_codes']}"
            if adapter_call_count_total == 0
            else f"live sequence status {sequence_status}; pilot promoted = {pilot_promoted}",
        }
    }

    ledger = Ledger()
    ledger.append(
        "live_sequence_start",
        {
            "run_id": run_id,
            "seed": seed,
            "include_dsh_pilot": include_dsh_pilot,
            "prereg_path": str(prereg_path),
        },
    )
    for name, path in child_artifacts.items():
        ledger.append("child_artifact", {"name": name, "path": path, "ledger_verified": child_ledgers_verified[name]})
    ledger.append(
        "promotion_decision",
        {
            "include_dsh_pilot": include_dsh_pilot,
            "smoke_hidden_verifier_pass_count": smoke_metrics["hidden_verifier_pass_count"],
            "pilot_promoted": pilot_promoted,
            "sequence_status": sequence_status,
        },
    )
    ledger.append("live_sequence_metrics", metrics)

    _write_json(artifact_path / "manifest.json", manifest)
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics, manifest))

    return LiveSequenceResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
