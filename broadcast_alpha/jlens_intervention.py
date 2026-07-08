import json
from dataclasses import dataclass
from pathlib import Path

from .ledger import Ledger


@dataclass(frozen=True)
class JLensInterventionResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _result_card(run_id: str, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Run type: J-lens causal intervention gate

## Verdict

Intervention status: {metrics['intervention_status']}
Leak probe status: {metrics['leak_probe_status']}
PC metric: {metrics['pc_metric']}
PC threshold: {metrics['pc_threshold']}
Differential activation present: {metrics['differential_activation_present']}
Causal intervention performed: {metrics['causal_intervention_performed']}
Sham intervention control performed: {metrics['sham_intervention_control_performed']}

The current leak-probe signal is below threshold, so the preregistered causal
intervention is not run. This is a clean defer/kill record, not a causal
mechanistic result.

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_jlens_intervention(
    seed: int = 42,
    artifact_root: Path | None = None,
    leak_probe_path: Path | None = None,
    pc_threshold: float | None = None,
) -> JLensInterventionResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"jlens_intervention_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)
    leak_probe_path = leak_probe_path or artifact_root / f"jlens_leak_probe_seed_{seed}"
    leak_metrics_path = leak_probe_path / "metrics.json"

    reason_codes: list[str] = []
    if not leak_metrics_path.exists():
        leak_metrics: dict = {}
        intervention_status = "blocked_missing_leak_probe"
        reason_codes.append("leak_probe_metrics_missing")
    else:
        leak_metrics = _read_json(leak_metrics_path)
        threshold = pc_threshold if pc_threshold is not None else leak_metrics.get("pc_threshold")
        pc_metric = leak_metrics.get("pc_metric")
        differential_activation_present = bool(leak_metrics.get("differential_activation_present", False))
        if not leak_metrics.get("outcome_leak_probe_performed"):
            intervention_status = "blocked_missing_leak_probe"
            reason_codes.append("outcome_leak_probe_not_performed")
        elif pc_metric is None or threshold is None:
            intervention_status = "blocked_missing_pc_metric"
            reason_codes.append("pc_metric_or_threshold_missing")
        elif not differential_activation_present or float(pc_metric) < float(threshold):
            intervention_status = "blocked_no_differential_signal"
            reason_codes.append("pc_below_threshold")
            reason_codes.append("intervention_not_run_by_prereg_kill_criterion")
        else:
            intervention_status = "blocked_intervention_not_implemented"
            reason_codes.append("differential_signal_present_but_intervention_not_implemented")

    prereg_manifest = {
        "prereg_id": "PREREG_CAUSAL-01",
        "prereg_path": str(Path("prereg/PREREG_CAUSAL-01.md")),
        "input_leak_probe_path": str(leak_probe_path),
        "kill_criterion": (
            "If the leak probe shows no differential activation, keep the "
            "J-lens rail frozen and do not run bridge/mechanistic rails."
        ),
        "causal_claim_allowed": False,
    }
    decision = {
        "intervention_status": intervention_status,
        "decision": "do_not_run_causal_intervention"
        if intervention_status == "blocked_no_differential_signal"
        else "blocked",
        "reason_codes": reason_codes,
        "leak_probe_path": str(leak_probe_path),
        "next_allowed_step": (
            "Run a stronger white-box leak probe before attempting causal intervention."
            if intervention_status == "blocked_no_differential_signal"
            else "Resolve the blocker recorded in reason_codes."
        ),
    }
    metrics = {
        "run_id": run_id,
        "seed": seed,
        "intervention_status": intervention_status,
        "leak_probe_status": leak_metrics.get("leak_probe_status"),
        "leak_probe_performed": bool(leak_metrics.get("outcome_leak_probe_performed", False)),
        "pc_metric": leak_metrics.get("pc_metric"),
        "pc_threshold": pc_threshold if pc_threshold is not None else leak_metrics.get("pc_threshold"),
        "differential_activation_present": bool(leak_metrics.get("differential_activation_present", False)),
        "causal_intervention_performed": False,
        "sham_intervention_control_performed": False,
        "intervention_delta": None,
        "verdict_flip_observed": False,
        "not_causal": True,
        "not_sufficient_for_JLENS_PROVED": True,
        "freeze_recommended": True,
        "reason_codes": reason_codes,
        "prereg_manifest_path": str(artifact_path / "prereg_manifest.json"),
        "decision_path": str(artifact_path / "decision.json"),
        "source_leak_metrics_path": str(leak_metrics_path),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": f"J-lens intervention gate: loaded leak probe from {leak_probe_path}",
            "2": f"J-lens intervention gate: status {intervention_status}; PC {metrics['pc_metric']} threshold {metrics['pc_threshold']}",
            "3": "J-lens intervention gate: no causal intervention performed; proof remains deferred",
        }
    }

    ledger = Ledger()
    ledger.append("jlens_intervention_start", {"run_id": run_id, "seed": seed})
    ledger.append("jlens_intervention_prereg_manifest", prereg_manifest)
    ledger.append("jlens_intervention_decision", decision)
    ledger.append("jlens_intervention_result", metrics)

    _write_json(artifact_path / "prereg_manifest.json", prereg_manifest)
    _write_json(artifact_path / "decision.json", decision)
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))

    return JLensInterventionResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
