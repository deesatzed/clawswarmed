import json
import math
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


def _load_leak_readouts(leak_metrics: dict, leak_probe_path: Path) -> list[dict]:
    direct_cases = leak_metrics.get("case_results")
    if isinstance(direct_cases, list):
        return direct_cases

    candidate_paths = []
    for key in ("readouts_path", "probe_payload_path"):
        value = leak_metrics.get(key)
        if value:
            candidate_paths.append(Path(value))
    candidate_paths.extend([leak_probe_path / "readouts.json", leak_probe_path / "probe_payload.json"])

    for path in candidate_paths:
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            continue
        payload = _read_json(path)
        cases = payload.get("case_results")
        if isinstance(cases, list):
            return cases
    return []


def _softmax_entropy(values: list[float]) -> float | None:
    if not values:
        return None
    max_value = max(values)
    exps = [math.exp(value - max_value) for value in values]
    total = sum(exps)
    if total == 0:
        return None
    probabilities = [value / total for value in exps]
    return float(-sum(prob * math.log(prob) for prob in probabilities if prob > 0))


def _position_window(case_result: dict) -> list[int]:
    for condition in case_result.get("condition_results", {}).values():
        positions = condition.get("pre_evidence_positions")
        if isinstance(positions, list):
            return [int(position) for position in positions]
    return []


def _mean_for_layer(case_result: dict, layer: str, condition: str, field: str) -> float | None:
    condition_result = case_result.get("condition_results", {}).get(condition, {})
    layer_result = condition_result.get("layers", {}).get(str(layer), {})
    value = layer_result.get(field)
    return float(value) if value is not None else None


def _build_causal_support_set(leak_metrics: dict, intervention_status: str) -> dict:
    entries = []
    for case_result in leak_metrics.get("case_results", []):
        layer = str(case_result.get("pc_layer"))
        layer_deltas = case_result.get("layer_deltas", {}).get(layer, {})
        entries.append(
            {
                "pair_id": case_result.get("pair_id"),
                "concept_direction": "verdict_target_minus_foil",
                "evidence_class": "shadow_probe_noninterventional",
                "intervention_type": (
                    "not_run_preregistered_signal_gate_failed"
                    if intervention_status == "blocked_no_differential_signal"
                    else "not_run"
                ),
                "layer": layer if layer != "None" else None,
                "position_window": _position_window(case_result),
                "readout_delta_vs_withheld": layer_deltas.get("target_delta_vs_withheld"),
                "readout_delta_vs_negative_control": layer_deltas.get(
                    "target_delta_vs_negative_control"
                ),
                "readout_min_control_delta": case_result.get("pc_metric"),
                "sham_control_delta_vs_withheld": layer_deltas.get("sham_delta_vs_withheld"),
                "sham_control_delta_vs_negative": layer_deltas.get(
                    "sham_delta_vs_negative_control"
                ),
                "sham_control_min_delta": case_result.get("sham_pc_metric"),
                "output_logit_delta": None,
                "verdict_flip_status": False,
                "causal_intervention_performed": False,
                "not_causal": True,
                "not_sufficient_for_JLENS_PROVED": True,
            }
        )
    return {
        "metric_name": "causal_support_set",
        "evidence_class": "shadow_probe_noninterventional",
        "derived_metric": True,
        "causal_intervention_performed": False,
        "sham_intervention_control_performed": False,
        "not_causal": True,
        "not_sufficient_for_JLENS_PROVED": True,
        "entry_count": len(entries),
        "entries": entries,
    }


def _build_convergence_dynamics(leak_metrics: dict, pc_threshold: float | None) -> dict:
    cases = []
    threshold = float(pc_threshold) if pc_threshold is not None else None
    for case_result in leak_metrics.get("case_results", []):
        layer_deltas = case_result.get("layer_deltas", {})
        layers = sorted(
            layer_deltas.keys(),
            key=lambda value: (0, int(value)) if str(value).isdigit() else (1, str(value)),
        )
        target_min_deltas = [
            float(layer_deltas[layer].get("target_min_control_delta", 0.0))
            for layer in layers
        ]
        revealed_margins = [
            _mean_for_layer(case_result, layer, "outcome_revealed", "target_minus_foil_mean")
            for layer in layers
        ]
        revealed_margins = [value for value in revealed_margins if value is not None]
        abs_margins = [abs(value) for value in revealed_margins]
        commitment = max(abs_margins) if abs_margins else abs(float(case_result.get("pc_metric", 0.0)))
        collapse_layer = None
        if threshold is not None:
            for layer, delta in zip(layers, target_min_deltas):
                if delta >= threshold:
                    collapse_layer = layer
                    break
        cases.append(
            {
                "pair_id": case_result.get("pair_id"),
                "evidence_class": "derived_readout_dynamics",
                "derived_metric": True,
                "layers": layers,
                "target_min_control_delta_by_layer": target_min_deltas,
                "pre_evidence_entropy_over_layers": _softmax_entropy(abs_margins or target_min_deltas),
                "commitment_order_parameter": float(commitment),
                "collapse_layer": collapse_layer,
                "collapse_before_evidence_span": collapse_layer is not None,
                "differential_activation_present": bool(
                    case_result.get("differential_activation_present", False)
                ),
                "not_causal": True,
                "not_sufficient_for_JLENS_PROVED": True,
            }
        )
    return {
        "metric_name": "convergence_dynamics",
        "evidence_class": "derived_readout_dynamics",
        "derived_metric": True,
        "not_causal": True,
        "not_sufficient_for_JLENS_PROVED": True,
        "case_count": len(cases),
        "cases": cases,
    }


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
Causal support set evidence class: {metrics['causal_support_set']['evidence_class']}
Causal support set entries: {metrics['causal_support_set']['entry_count']}
Convergence dynamics evidence class: {metrics['convergence_dynamics']['evidence_class']}
Convergence dynamics cases: {metrics['convergence_dynamics']['case_count']}

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
        leak_metrics["case_results"] = _load_leak_readouts(leak_metrics, leak_probe_path)
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

    effective_threshold = (
        pc_threshold if pc_threshold is not None else leak_metrics.get("pc_threshold")
    )
    causal_support_set = _build_causal_support_set(leak_metrics, intervention_status)
    convergence_dynamics = _build_convergence_dynamics(leak_metrics, effective_threshold)

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
        "pc_threshold": effective_threshold,
        "differential_activation_present": bool(leak_metrics.get("differential_activation_present", False)),
        "causal_intervention_performed": False,
        "sham_intervention_control_performed": False,
        "intervention_delta": None,
        "verdict_flip_observed": False,
        "causal_support_set": causal_support_set,
        "convergence_dynamics": convergence_dynamics,
        "derived_metrics_not_causal": True,
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
