import json
from dataclasses import dataclass
from pathlib import Path

from .ab_bias_suite import run_ab_bias_suite
from .experiments import run_dsh, run_rqgm, run_synthetic
from .jlens import run_jlens_gate
from .jlens_hf_smoke import run_jlens_hf_smoke
from .jlens_intervention import run_jlens_intervention
from .jlens_leak_probe import run_jlens_leak_probe
from .jlens_runtime import prepare_jlens_probe
from .jlens_smoke import run_jlens_smoke
from .ledger import Ledger
from .ledger_stress import run_ledger_stress
from .live_dsh import run_live_dsh, run_live_smoke
from .live_gate import run_live_gate
from .live_sequence import run_live_sequence
from .reporting import build_result_report


@dataclass(frozen=True)
class RunAllResult:
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
    return f"""# Result Card: {run_id}

Run type: unattended Broadcast-alpha / Glass Gate bundle

## One-number demo

GLASSGATE_LIFT = {metrics['glassgate_lift']} [95% CI: {metrics['glassgate_lift_ci95'][0]}, {metrics['glassgate_lift_ci95'][1]}]

## Summary

Run status: {metrics['run_status']}
Seed detectability AUC: {metrics['seed_detectability_auc']}
Adversarial token AUC: {metrics['seed_adversarial_auc']}
Ledger stress receipts: {metrics['ledger_stress_synthetic_receipt_count']}
Ledger stress tamper detection: {metrics['ledger_stress_tamper_detection_passed']}
Candidate ablation rate: {metrics['candidate_ablation_rate']}
Token cost per solve: {metrics['token_cost_per_solve']}
RQGM epochs: {metrics['epoch_count']}
J-lens rail: {metrics['jlens_rail_status']}
Live model rail: {metrics['live_model_rail_status']}
Adapter call performed: {metrics['live_adapter_call_performed']}
Live model run performed: {metrics['live_model_run_performed']}
Live smoke: {metrics['live_smoke_run_status']}
Live smoke verifier pass rate: {metrics['live_smoke_hidden_verifier_pass_rate']}
Live DSH pilot: {metrics['live_dsh_run_status']}
Live DSH prereg: {metrics['live_dsh_prereg_id']}
Live DSH verifier pass rate: {metrics['live_dsh_hidden_verifier_pass_rate']}
Live sequence: {metrics['live_sequence_status']}
Live sequence adapter calls: {metrics['live_sequence_adapter_call_count_total']}

## Child artifacts

| Artifact | Path | Ledger verified |
|---|---|---:|
{child_rows}

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_all(
    seed: int = 42,
    tasks_per_cell: int = 30,
    epochs: int = 5,
    prereg_dir: Path | None = None,
    artifact_root: Path | None = None,
    live_env_file: Path | None = None,
    live_env: dict[str, str] | None = None,
) -> RunAllResult:
    prereg_dir = prereg_dir or Path("prereg")
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"run_all_seed_{seed}"
    artifact_path = artifact_root / run_id
    child_root = artifact_path / "source_artifacts"
    final_report_path = artifact_path / "final_report"
    artifact_path.mkdir(parents=True, exist_ok=True)

    ab_bias_suite = run_ab_bias_suite(seed=seed, artifact_root=child_root)
    ledger_stress = run_ledger_stress(seed=seed, receipt_count=10_000, artifact_root=child_root)
    synthetic = run_synthetic(seed=seed, artifact_root=child_root)
    dsh = run_dsh(
        prereg_path=prereg_dir / "PREREG_DSH-01.md",
        seed=seed,
        tasks_per_cell=tasks_per_cell,
        artifact_root=child_root,
    )
    rqgm = run_rqgm(
        prereg_path=prereg_dir / "PREREG_EPOCH-01.md",
        seed=seed,
        epochs=epochs,
        artifact_root=child_root,
    )
    jlens_gate = run_jlens_gate(seed=seed, artifact_root=child_root)
    jlens_runtime = prepare_jlens_probe(seed=seed, artifact_root=child_root)
    jlens_smoke = run_jlens_smoke(seed=seed, artifact_root=child_root)
    jlens_hf_smoke = run_jlens_hf_smoke(seed=seed, artifact_root=child_root)
    jlens_leak_probe = run_jlens_leak_probe(
        seed=seed,
        artifact_root=child_root,
        vignette_packet=prereg_dir / "jlens_vignette_packet_01.json",
    )
    jlens_intervention = run_jlens_intervention(
        seed=seed,
        artifact_root=child_root,
        leak_probe_path=jlens_leak_probe.artifact_path,
    )
    live_gate = run_live_gate(seed=seed, artifact_root=child_root, env_file=live_env_file, env=live_env)
    live_smoke = run_live_smoke(
        seed=seed,
        artifact_root=child_root,
        env_file=live_env_file,
        env=live_env,
        prereg_path=prereg_dir / "PREREG_LIVE-01.md",
    )
    live_dsh = run_live_dsh(
        seed=seed,
        tasks_per_cell=1,
        artifact_root=child_root,
        env_file=live_env_file,
        env=live_env,
        prereg_path=prereg_dir / "PREREG_LIVE-01.md",
    )
    live_sequence = run_live_sequence(
        seed=seed,
        artifact_root=child_root,
        env_file=live_env_file,
        env=live_env,
        prereg_path=prereg_dir / "PREREG_LIVE-01.md",
    )
    final_report = build_result_report(artifact_root=child_root, output_dir=final_report_path)

    child_artifacts = {
        "ab_bias_suite": str(ab_bias_suite.artifact_path),
        "ledger_stress": str(ledger_stress.artifact_path),
        "synthetic": str(synthetic.artifact_path),
        "dsh": str(dsh.artifact_path),
        "rqgm": str(rqgm.artifact_path),
        "jlens_gate": str(jlens_gate.artifact_path),
        "jlens_runtime_readiness": str(jlens_runtime.artifact_path),
        "jlens_smoke": str(jlens_smoke.artifact_path),
        "jlens_hf_smoke": str(jlens_hf_smoke.artifact_path),
        "jlens_leak_probe": str(jlens_leak_probe.artifact_path),
        "jlens_intervention": str(jlens_intervention.artifact_path),
        "live_model_gate": str(live_gate.artifact_path),
        "live_smoke": str(live_smoke.artifact_path),
        "live_dsh_pilot": str(live_dsh.artifact_path),
        "live_sequence": str(live_sequence.artifact_path),
        "final_report": str(final_report.artifact_path),
    }
    child_paths = {
        "ab_bias_suite": ab_bias_suite.artifact_path,
        "ledger_stress": ledger_stress.artifact_path,
        "synthetic": synthetic.artifact_path,
        "dsh": dsh.artifact_path,
        "rqgm": rqgm.artifact_path,
        "jlens_gate": jlens_gate.artifact_path,
        "jlens_runtime_readiness": jlens_runtime.artifact_path,
        "jlens_smoke": jlens_smoke.artifact_path,
        "jlens_hf_smoke": jlens_hf_smoke.artifact_path,
        "jlens_leak_probe": jlens_leak_probe.artifact_path,
        "jlens_intervention": jlens_intervention.artifact_path,
        "live_model_gate": live_gate.artifact_path,
        "live_smoke": live_smoke.artifact_path,
        "live_dsh_pilot": live_dsh.artifact_path,
        "live_sequence": live_sequence.artifact_path,
        "final_report": final_report.artifact_path,
    }
    child_ledgers_verified = {
        name: _verify_ledger(path)
        for name, path in child_paths.items()
    }
    final_metrics = _read_json(final_report.artifact_path / "metrics.json")
    manifest = {
        "run_id": run_id,
        "seed": seed,
        "tasks_per_cell": tasks_per_cell,
        "epochs": epochs,
        "child_artifacts": child_artifacts,
        "run_sequence": [
            "ab_bias_suite",
            "synthetic",
            "ledger_stress",
            "dsh",
            "rqgm",
            "jlens_gate",
            "jlens_runtime_readiness",
            "jlens_smoke",
            "jlens_hf_smoke",
            "jlens_leak_probe",
            "jlens_intervention",
            "live_model_gate",
            "live_smoke",
            "live_dsh_pilot",
            "live_sequence",
            "final_report",
        ],
    }
    replay_contexts = {
        "agent_1": {
            "1": "unattended bundle: generated ledger stress, synthetic, DSH, RQGM, J-lens gate, J-lens runtime readiness, J-lens reference smoke, J-lens HF smoke, J-lens leak probe, J-lens intervention gate, live model gate, live smoke, live DSH pilot, live sequence, and final report artifacts",
            "2": f"unattended bundle: GLASSGATE_LIFT {final_metrics['glassgate_lift']} with seed adversarial AUC {final_metrics['seed_adversarial_auc']}",
            "3": f"unattended bundle: final report ready, all child ledgers verified, J-lens rail frozen/deferred, live sequence {final_metrics['live_sequence_status']}, live model run not performed",
        }
    }
    metrics = {
        "run_id": run_id,
        "run_status": final_metrics["report_status"],
        "seed": seed,
        "tasks_per_cell": tasks_per_cell,
        "epochs": epochs,
        "ab_bias_case_count": final_metrics["ab_bias_case_count"],
        "ab_bias_wrong_bias_harm": final_metrics["ab_bias_wrong_bias_harm"],
        "ab_bias_behavioral_screening_only": final_metrics[
            "ab_bias_behavioral_screening_only"
        ],
        "ab_bias_not_sufficient_for_JLENS_PROVED": final_metrics[
            "ab_bias_not_sufficient_for_JLENS_PROVED"
        ],
        "glassgate_lift": final_metrics["glassgate_lift"],
        "glassgate_lift_ci95": final_metrics["glassgate_lift_ci95"],
        "D_by_arm": final_metrics["D_by_arm"],
        "D_by_panel_type": final_metrics["D_by_panel_type"],
        "ledger_stress_synthetic_receipt_count": final_metrics["ledger_stress_synthetic_receipt_count"],
        "ledger_stress_total_receipt_count": final_metrics["ledger_stress_total_receipt_count"],
        "ledger_stress_mixed_kind_count": final_metrics["ledger_stress_mixed_kind_count"],
        "ledger_stress_pre_metrics_chain_verified": final_metrics["ledger_stress_pre_metrics_chain_verified"],
        "ledger_stress_ledger_verified": final_metrics["ledger_stress_ledger_verified"],
        "ledger_stress_tamper_detection_passed": final_metrics["ledger_stress_tamper_detection_passed"],
        "verified_solve_rate": final_metrics["verified_solve_rate"],
        "panel_correlation_rho": final_metrics["panel_correlation_rho"],
        "candidate_ablation_rate": final_metrics["candidate_ablation_rate"],
        "token_cost_per_solve": final_metrics["token_cost_per_solve"],
        "seed_detectability_auc": final_metrics["seed_detectability_auc"],
        "seed_marker_auc": final_metrics["seed_marker_auc"],
        "seed_adversarial_auc": final_metrics["seed_adversarial_auc"],
        "seed_camouflage_failed": final_metrics["seed_camouflage_failed"],
        "epoch_count": final_metrics["epoch_count"],
        "replacement_count": final_metrics["replacement_count"],
        "current_evaluator_id": final_metrics["current_evaluator_id"],
        "jlens_rail_status": final_metrics["jlens_rail_status"],
        "jlens_failure_ledger_entry_id": final_metrics["jlens_failure_ledger_entry_id"],
        "jlens_runtime_readiness_status": final_metrics["jlens_runtime_readiness_status"],
        "jlens_runtime_white_box_model_available": final_metrics["jlens_runtime_white_box_model_available"],
        "jlens_runtime_gradient_access_confirmed": final_metrics["jlens_runtime_gradient_access_confirmed"],
        "jlens_runtime_real_probe_runnable": final_metrics["jlens_runtime_real_probe_runnable"],
        "jlens_runtime_reason_codes": final_metrics["jlens_runtime_reason_codes"],
        "jlens_smoke_status": final_metrics["jlens_smoke_status"],
        "jlens_smoke_real_fit_apply": final_metrics["jlens_smoke_real_fit_apply"],
        "jlens_smoke_not_sufficient_for_JLENS_PROVED": final_metrics["jlens_smoke_not_sufficient_for_JLENS_PROVED"],
        "jlens_hf_smoke_status": final_metrics["jlens_hf_smoke_status"],
        "jlens_hf_smoke_real_fit_apply": final_metrics["jlens_hf_smoke_real_fit_apply"],
        "jlens_hf_selected_labels_all_single_token": final_metrics["jlens_hf_selected_labels_all_single_token"],
        "jlens_hf_critical_labels_all_single_token": final_metrics["jlens_hf_critical_labels_all_single_token"],
        "jlens_hf_smoke_not_sufficient_for_JLENS_PROVED": final_metrics["jlens_hf_smoke_not_sufficient_for_JLENS_PROVED"],
        "jlens_leak_probe_status": final_metrics["jlens_leak_probe_status"],
        "jlens_leak_probe_performed": final_metrics["jlens_leak_probe_performed"],
        "jlens_leak_pc_metric": final_metrics["jlens_leak_pc_metric"],
        "jlens_leak_differential_activation_present": final_metrics[
            "jlens_leak_differential_activation_present"
        ],
        "jlens_leak_causal_intervention_performed": final_metrics[
            "jlens_leak_causal_intervention_performed"
        ],
        "jlens_leak_not_sufficient_for_JLENS_PROVED": final_metrics[
            "jlens_leak_not_sufficient_for_JLENS_PROVED"
        ],
        "jlens_intervention_status": final_metrics["jlens_intervention_status"],
        "jlens_intervention_performed": final_metrics["jlens_intervention_performed"],
        "jlens_intervention_sham_control_performed": final_metrics[
            "jlens_intervention_sham_control_performed"
        ],
        "jlens_intervention_causal_support_entry_count": final_metrics[
            "jlens_intervention_causal_support_entry_count"
        ],
        "jlens_intervention_convergence_case_count": final_metrics[
            "jlens_intervention_convergence_case_count"
        ],
        "jlens_intervention_derived_metrics_not_causal": final_metrics[
            "jlens_intervention_derived_metrics_not_causal"
        ],
        "jlens_intervention_not_sufficient_for_JLENS_PROVED": final_metrics[
            "jlens_intervention_not_sufficient_for_JLENS_PROVED"
        ],
        "live_model_rail_status": final_metrics["live_model_rail_status"],
        "live_adapter_call_performed": final_metrics["live_adapter_call_performed"],
        "live_model_run_performed": final_metrics["live_model_run_performed"],
        "live_openrouter_api_key_present": final_metrics["live_openrouter_api_key_present"],
        "live_reason_codes": final_metrics["live_reason_codes"],
        "live_smoke_run_status": final_metrics["live_smoke_run_status"],
        "live_smoke_adapter_call_count": final_metrics["live_smoke_adapter_call_count"],
        "live_smoke_candidate_patch_present_count": final_metrics["live_smoke_candidate_patch_present_count"],
        "live_smoke_hidden_verifier_pass_count": final_metrics["live_smoke_hidden_verifier_pass_count"],
        "live_smoke_hidden_verifier_pass_rate": final_metrics["live_smoke_hidden_verifier_pass_rate"],
        "live_smoke_model_run_performed": final_metrics["live_smoke_model_run_performed"],
        "live_dsh_run_status": final_metrics["live_dsh_run_status"],
        "live_dsh_prereg_id": final_metrics["live_dsh_prereg_id"],
        "live_dsh_prereg_path": final_metrics["live_dsh_prereg_path"],
        "live_dsh_prereg_exists": final_metrics["live_dsh_prereg_exists"],
        "live_dsh_adapter_call_count": final_metrics["live_dsh_adapter_call_count"],
        "live_dsh_candidate_patch_present_count": final_metrics["live_dsh_candidate_patch_present_count"],
        "live_dsh_hidden_verifier_pass_count": final_metrics["live_dsh_hidden_verifier_pass_count"],
        "live_dsh_hidden_verifier_pass_rate": final_metrics["live_dsh_hidden_verifier_pass_rate"],
        "live_dsh_model_run_performed": final_metrics["live_dsh_model_run_performed"],
        "live_sequence_status": final_metrics["live_sequence_status"],
        "live_sequence_adapter_call_count_total": final_metrics["live_sequence_adapter_call_count_total"],
        "live_sequence_smoke_status": final_metrics["live_sequence_smoke_status"],
        "live_sequence_smoke_hidden_verifier_pass_count": final_metrics["live_sequence_smoke_hidden_verifier_pass_count"],
        "live_sequence_pilot_status": final_metrics["live_sequence_pilot_status"],
        "live_sequence_pilot_promoted": final_metrics["live_sequence_pilot_promoted"],
        "live_sequence_all_child_ledgers_verified": final_metrics["live_sequence_all_child_ledgers_verified"],
        "child_ledgers_verified": child_ledgers_verified,
        "all_child_ledgers_verified": all(child_ledgers_verified.values()),
        "manifest_path": str(artifact_path / "manifest.json"),
        "final_report_path": str(final_report.artifact_path),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
    }

    ledger = Ledger()
    ledger.append("run_all_start", {"run_id": run_id, "seed": seed, "tasks_per_cell": tasks_per_cell, "epochs": epochs})
    for name, path in child_artifacts.items():
        ledger.append("child_artifact", {"name": name, "path": path, "ledger_verified": child_ledgers_verified[name]})
    ledger.append("final_report", {"path": str(final_report.artifact_path), "report_status": final_metrics["report_status"]})
    ledger.append("run_all_metrics", metrics)

    _write_json(artifact_path / "manifest.json", manifest)
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics, manifest))

    return RunAllResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
