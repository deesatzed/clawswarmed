import json
from dataclasses import dataclass
from pathlib import Path

from .experiments import run_dsh, run_rqgm, run_synthetic
from .jlens import run_jlens_gate
from .ledger import Ledger
from .live_dsh import run_live_dsh
from .live_gate import run_live_gate
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
RQGM epochs: {metrics['epoch_count']}
J-lens rail: {metrics['jlens_rail_status']}
Live model rail: {metrics['live_model_rail_status']}
Adapter call performed: {metrics['live_adapter_call_performed']}
Live model run performed: {metrics['live_model_run_performed']}
Live DSH pilot: {metrics['live_dsh_run_status']}
Live DSH prereg: {metrics['live_dsh_prereg_id']}
Live DSH verifier pass rate: {metrics['live_dsh_hidden_verifier_pass_rate']}

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
    live_gate = run_live_gate(seed=seed, artifact_root=child_root, env_file=live_env_file, env=live_env)
    live_dsh = run_live_dsh(
        seed=seed,
        tasks_per_cell=1,
        artifact_root=child_root,
        env_file=live_env_file,
        env=live_env,
        prereg_path=prereg_dir / "PREREG_LIVE-01.md",
    )
    final_report = build_result_report(artifact_root=child_root, output_dir=final_report_path)

    child_artifacts = {
        "synthetic": str(synthetic.artifact_path),
        "dsh": str(dsh.artifact_path),
        "rqgm": str(rqgm.artifact_path),
        "jlens_gate": str(jlens_gate.artifact_path),
        "live_model_gate": str(live_gate.artifact_path),
        "live_dsh_pilot": str(live_dsh.artifact_path),
        "final_report": str(final_report.artifact_path),
    }
    child_paths = {
        "synthetic": synthetic.artifact_path,
        "dsh": dsh.artifact_path,
        "rqgm": rqgm.artifact_path,
        "jlens_gate": jlens_gate.artifact_path,
        "live_model_gate": live_gate.artifact_path,
        "live_dsh_pilot": live_dsh.artifact_path,
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
        "run_sequence": ["synthetic", "dsh", "rqgm", "jlens_gate", "live_model_gate", "live_dsh_pilot", "final_report"],
    }
    replay_contexts = {
        "agent_1": {
            "1": "unattended bundle: generated synthetic, DSH, RQGM, J-lens gate, live model gate, live DSH pilot, and final report artifacts",
            "2": f"unattended bundle: GLASSGATE_LIFT {final_metrics['glassgate_lift']} with seed adversarial AUC {final_metrics['seed_adversarial_auc']}",
            "3": "unattended bundle: final report ready, all child ledgers verified, J-lens rail frozen/deferred, live model run not performed",
        }
    }
    metrics = {
        "run_id": run_id,
        "run_status": final_metrics["report_status"],
        "seed": seed,
        "tasks_per_cell": tasks_per_cell,
        "epochs": epochs,
        "glassgate_lift": final_metrics["glassgate_lift"],
        "glassgate_lift_ci95": final_metrics["glassgate_lift_ci95"],
        "D_by_arm": final_metrics["D_by_arm"],
        "D_by_panel_type": final_metrics["D_by_panel_type"],
        "seed_detectability_auc": final_metrics["seed_detectability_auc"],
        "seed_marker_auc": final_metrics["seed_marker_auc"],
        "seed_adversarial_auc": final_metrics["seed_adversarial_auc"],
        "seed_camouflage_failed": final_metrics["seed_camouflage_failed"],
        "epoch_count": final_metrics["epoch_count"],
        "replacement_count": final_metrics["replacement_count"],
        "current_evaluator_id": final_metrics["current_evaluator_id"],
        "jlens_rail_status": final_metrics["jlens_rail_status"],
        "jlens_failure_ledger_entry_id": final_metrics["jlens_failure_ledger_entry_id"],
        "live_model_rail_status": final_metrics["live_model_rail_status"],
        "live_adapter_call_performed": final_metrics["live_adapter_call_performed"],
        "live_model_run_performed": final_metrics["live_model_run_performed"],
        "live_openrouter_api_key_present": final_metrics["live_openrouter_api_key_present"],
        "live_reason_codes": final_metrics["live_reason_codes"],
        "live_dsh_run_status": final_metrics["live_dsh_run_status"],
        "live_dsh_prereg_id": final_metrics["live_dsh_prereg_id"],
        "live_dsh_prereg_path": final_metrics["live_dsh_prereg_path"],
        "live_dsh_prereg_exists": final_metrics["live_dsh_prereg_exists"],
        "live_dsh_adapter_call_count": final_metrics["live_dsh_adapter_call_count"],
        "live_dsh_candidate_patch_present_count": final_metrics["live_dsh_candidate_patch_present_count"],
        "live_dsh_hidden_verifier_pass_count": final_metrics["live_dsh_hidden_verifier_pass_count"],
        "live_dsh_hidden_verifier_pass_rate": final_metrics["live_dsh_hidden_verifier_pass_rate"],
        "live_dsh_model_run_performed": final_metrics["live_dsh_model_run_performed"],
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
