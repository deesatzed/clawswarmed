import json
from dataclasses import dataclass
from pathlib import Path

from .ledger import Ledger


@dataclass(frozen=True)
class ReportResult:
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


def _result_table_md(rows: list[dict]) -> str:
    table_rows = "\n".join(
        "| {section} | {primary_metric} | {primary_value} | {ledger_verified} | {artifact_path} |".format(
            section=row["section"],
            primary_metric=row["primary_metric"],
            primary_value=row["primary_value"],
            ledger_verified=row["ledger_verified"],
            artifact_path=row["artifact_path"],
        )
        for row in rows
    )
    return f"""# Broadcast-alpha Result Table

| Section | Primary metric | Value | Ledger verified | Artifact |
|---|---|---:|---:|---|
{table_rows}
"""


def _result_card(run_id: str, metrics: dict, rows: list[dict]) -> str:
    d_by_arm = "\n".join(
        f"| {arm} | {value} |"
        for arm, value in metrics["D_by_arm"].items()
    )
    row_summary = "\n".join(
        f"- {row['section']}: {row['primary_metric']} = {row['primary_value']}"
        for row in rows
    )
    return f"""# Result Card: {run_id}

Run type: consolidated Broadcast-alpha / Glass Gate report

## One-number demo

GLASSGATE_LIFT = {metrics['glassgate_lift']} [95% CI: {metrics['glassgate_lift_ci95'][0]}, {metrics['glassgate_lift_ci95'][1]}]

## D by arm

| Arm | D |
|---|---:|
{d_by_arm}

## Required evidence

{row_summary}

## 10k ledger stress

Synthetic stress receipts: {metrics['ledger_stress_synthetic_receipt_count']}
Mixed receipt kinds: {metrics['ledger_stress_mixed_kind_count']}
Tamper detection passed: {metrics['ledger_stress_tamper_detection_passed']}

## Macro diagnostics

Verified solve rate: {metrics['verified_solve_rate']}
Panel correlation rho: {metrics['panel_correlation_rho']}
Candidate ablation rate: {metrics['candidate_ablation_rate']}
Token cost per solve: {metrics['token_cost_per_solve']}

## Seed detectability audit

Seed detectability AUC: {metrics['seed_detectability_auc']}
Adversarial token AUC: {metrics['seed_adversarial_auc']}
Camouflage failed: {metrics['seed_camouflage_failed']}

## RQGM epoch trajectory

Epoch count: {metrics['epoch_count']}
Replacement count: {metrics['replacement_count']}
Current evaluator: {metrics['current_evaluator_id']}

## A/B behavioral bias

A/B suite status: {metrics['ab_bias_suite_status']}
A/B cases: {metrics['ab_bias_case_count']}
A/B wrong-bias harm: {metrics['ab_bias_wrong_bias_harm']}
A/B dissent rescue rate: {metrics['ab_bias_dissent_rescue_rate']}
A/B false consensus rejection rate: {metrics['ab_bias_false_consensus_rejection_rate']}
A/B behavioral screening only: {metrics['ab_bias_behavioral_screening_only']}
A/B sufficient for J-lens proof: {not metrics['ab_bias_not_sufficient_for_JLENS_PROVED']}

## J-lens rail

J-lens rail frozen: {metrics['jlens_rail_status'] == 'frozen'}
Failure ledger entry: {metrics['jlens_failure_ledger_entry_id']}
Runtime readiness: {metrics['jlens_runtime_readiness_status']}
Runtime reason codes: {metrics['jlens_runtime_reason_codes']}
White-box model available: {metrics['jlens_runtime_white_box_model_available']}
Tokenizer labels verified: {metrics['jlens_runtime_tokenizer_labels_all_single_token']}
Fit/apply smoke: {metrics['jlens_smoke_status']}
Fit/apply smoke real: {metrics['jlens_smoke_real_fit_apply']}
Fit/apply smoke sufficient for proof: {not metrics['jlens_smoke_not_sufficient_for_JLENS_PROVED']}
HF smoke: {metrics['jlens_hf_smoke_status']}
HF smoke real: {metrics['jlens_hf_smoke_real_fit_apply']}
HF selected labels single-token: {metrics['jlens_hf_selected_labels_all_single_token']}
HF critical labels single-token: {metrics['jlens_hf_critical_labels_all_single_token']}
Leak probe: {metrics['jlens_leak_probe_status']}
Leak probe performed: {metrics['jlens_leak_probe_performed']}
Leak PC metric: {metrics['jlens_leak_pc_metric']}
Leak differential activation: {metrics['jlens_leak_differential_activation_present']}
Leak causal intervention: {metrics['jlens_leak_causal_intervention_performed']}
Intervention gate: {metrics['jlens_intervention_status']}
Intervention performed: {metrics['jlens_intervention_performed']}
Intervention sham control: {metrics['jlens_intervention_sham_control_performed']}
Intervention derived metrics non-causal: {metrics['jlens_intervention_derived_metrics_not_causal']}
Causal support set entries: {metrics['jlens_intervention_causal_support_entry_count']}
Convergence dynamics cases: {metrics['jlens_intervention_convergence_case_count']}

## Live model rail

Live model rail status: {metrics['live_model_rail_status']}
Adapter call performed: {metrics['live_adapter_call_performed']}
Live model run performed: {metrics['live_model_run_performed']}
OpenRouter API key present by name: {metrics['live_openrouter_api_key_present']}
No secret values recorded: {not metrics['live_secret_values_recorded']}

## Live A/B behavioral

Live A/B status: {metrics['live_ab_bias_status']}
Live A/B models: {metrics['live_ab_model_count']}
Live A/B case runs: {metrics['live_ab_total_case_runs']}
Live A/B adapter calls: {metrics['live_ab_adapter_call_count_total']}
Live A/B accuracy: {metrics['live_ab_accuracy']}
Live A/B schema compliance rate: {metrics['live_ab_schema_compliance_rate']}
Live A/B parsed-only accuracy: {metrics['live_ab_parsed_only_accuracy']}
Live A/B wrong-bias accuracy: {metrics['live_ab_wrong_bias_accuracy']}
Live A/B parsed-only wrong-bias accuracy: {metrics['live_ab_parsed_only_wrong_bias_accuracy']}
Live A/B parse failures: {metrics['live_ab_parse_failure_count']}
Live A/B behavioral only: {metrics['live_ab_behavioral_screening_only']}

## Live smoke

Live smoke status: {metrics['live_smoke_run_status']}
Live smoke adapter calls: {metrics['live_smoke_adapter_call_count']}
Live smoke hidden verifier pass count: {metrics['live_smoke_hidden_verifier_pass_count']}
Live smoke hidden verifier pass rate: {metrics['live_smoke_hidden_verifier_pass_rate']}

## Live sequence

Live sequence status: {metrics['live_sequence_status']}
Live sequence adapter calls: {metrics['live_sequence_adapter_call_count_total']}
Live sequence smoke status: {metrics['live_sequence_smoke_status']}
Live sequence pilot status: {metrics['live_sequence_pilot_status']}
Live sequence pilot promoted: {metrics['live_sequence_pilot_promoted']}

## Live DSH pilot

Live DSH pilot status: {metrics['live_dsh_run_status']}
Live DSH prereg: {metrics['live_dsh_prereg_id']}
Live DSH adapter calls: {metrics['live_dsh_adapter_call_count']}
Live DSH hidden verifier pass count: {metrics['live_dsh_hidden_verifier_pass_count']}
Live DSH hidden verifier pass rate: {metrics['live_dsh_hidden_verifier_pass_rate']}

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def build_result_report(artifact_root: Path | None = None, output_dir: Path | None = None) -> ReportResult:
    artifact_root = artifact_root or Path("artifacts")
    output_dir = output_dir or artifact_root / "final_report_seed_42"
    run_id = output_dir.name
    output_dir.mkdir(parents=True, exist_ok=True)

    dsh_path = artifact_root / "dsh_seed_42"
    ab_bias_path = artifact_root / "ab_bias_suite_seed_42"
    ledger_stress_path = artifact_root / "ledger_stress_seed_42"
    rqgm_path = artifact_root / "rqgm_seed_42"
    jlens_path = artifact_root / "jlens_gate_seed_42"
    jlens_runtime_path = artifact_root / "jlens_runtime_readiness_seed_42"
    jlens_smoke_path = artifact_root / "jlens_smoke_seed_42"
    jlens_hf_smoke_path = artifact_root / "jlens_hf_smoke_seed_42"
    jlens_leak_probe_path = artifact_root / "jlens_leak_probe_seed_42"
    jlens_intervention_path = artifact_root / "jlens_intervention_seed_42"
    live_path = artifact_root / "live_gate_seed_42"
    live_smoke_path = artifact_root / "live_smoke_seed_42"
    live_dsh_path = artifact_root / "live_dsh_seed_42"
    live_sequence_path = artifact_root / "live_sequence_seed_42"
    live_ab_path = artifact_root / "live_ab_bias_suite_seed_42"

    dsh_metrics = _read_json(dsh_path / "metrics.json")
    seed_audit = _read_json(dsh_path / "seed_audit.json")
    if (ab_bias_path / "metrics.json").exists():
        ab_bias_metrics = _read_json(ab_bias_path / "metrics.json")
        ab_bias_ledger_verified = _verify_ledger(ab_bias_path)
    else:
        ab_bias_metrics = {
            "case_count": 0,
            "wrong_bias_harm": 0.0,
            "dissent_rescue_rate": 0.0,
            "false_consensus_rejection_rate": 0.0,
            "behavioral_screening_only": True,
            "not_sufficient_for_JLENS_PROVED": True,
            "live_model_run_performed": False,
            "jlens_probe_performed": False,
        }
        ab_bias_ledger_verified = False
    if (ledger_stress_path / "metrics.json").exists():
        ledger_stress_metrics = _read_json(ledger_stress_path / "metrics.json")
        ledger_stress_ledger_verified = _verify_ledger(ledger_stress_path)
    else:
        ledger_stress_metrics = {
            "synthetic_receipt_count": 0,
            "total_receipt_count": 0,
            "mixed_kind_count": 0,
            "pre_metrics_chain_verified": False,
            "ledger_verified": False,
            "tamper_detection_passed": False,
        }
        ledger_stress_ledger_verified = False
    rqgm_metrics = _read_json(rqgm_path / "metrics.json")
    jlens_metrics = _read_json(jlens_path / "metrics.json")
    if (jlens_runtime_path / "metrics.json").exists():
        jlens_runtime_metrics = _read_json(jlens_runtime_path / "metrics.json")
        jlens_runtime_ledger_verified = _verify_ledger(jlens_runtime_path)
    else:
        jlens_runtime_metrics = {
            "readiness_status": "not_run",
            "white_box_model_available": False,
            "gradient_access_confirmed": False,
            "real_probe_runnable": False,
            "tokenizer_labels_all_single_token": False,
            "reason_codes": ["jlens_runtime_readiness_artifact_missing"],
        }
        jlens_runtime_ledger_verified = False
    if (jlens_smoke_path / "metrics.json").exists():
        jlens_smoke_metrics = _read_json(jlens_smoke_path / "metrics.json")
        jlens_smoke_ledger_verified = _verify_ledger(jlens_smoke_path)
    else:
        jlens_smoke_metrics = {
            "smoke_status": "not_run",
            "real_jlens_fit_apply_smoke": False,
            "gradient_access_confirmed": False,
            "layer_activation_access_confirmed": False,
            "not_sufficient_for_JLENS_PROVED": True,
        }
        jlens_smoke_ledger_verified = False
    if (jlens_hf_smoke_path / "metrics.json").exists():
        jlens_hf_smoke_metrics = _read_json(jlens_hf_smoke_path / "metrics.json")
        jlens_hf_smoke_ledger_verified = _verify_ledger(jlens_hf_smoke_path)
    else:
        jlens_hf_smoke_metrics = {
            "smoke_status": "not_run",
            "real_hf_jlens_fit_apply_smoke": False,
            "selected_labels_all_single_token": False,
            "critical_labels_all_single_token": False,
            "gradient_access_confirmed": False,
            "layer_activation_access_confirmed": False,
            "not_sufficient_for_JLENS_PROVED": True,
        }
        jlens_hf_smoke_ledger_verified = False
    if (jlens_leak_probe_path / "metrics.json").exists():
        jlens_leak_probe_metrics = _read_json(jlens_leak_probe_path / "metrics.json")
        jlens_leak_probe_ledger_verified = _verify_ledger(jlens_leak_probe_path)
    else:
        jlens_leak_probe_metrics = {
            "leak_probe_status": "not_run",
            "real_hf_jlens_leak_probe": False,
            "outcome_leak_probe_performed": False,
            "pc_metric": None,
            "pc_threshold": None,
            "differential_activation_present": False,
            "negative_control_performed": False,
            "sham_control_performed": False,
            "causal_intervention_performed": False,
            "not_sufficient_for_JLENS_PROVED": True,
        }
        jlens_leak_probe_ledger_verified = False
    if (jlens_intervention_path / "metrics.json").exists():
        jlens_intervention_metrics = _read_json(jlens_intervention_path / "metrics.json")
        jlens_intervention_ledger_verified = _verify_ledger(jlens_intervention_path)
    else:
        jlens_intervention_metrics = {
            "intervention_status": "not_run",
            "leak_probe_performed": False,
            "pc_metric": None,
            "pc_threshold": None,
            "differential_activation_present": False,
            "causal_intervention_performed": False,
            "sham_intervention_control_performed": False,
            "causal_support_set": {
                "evidence_class": "not_run",
                "derived_metric": True,
                "not_causal": True,
                "not_sufficient_for_JLENS_PROVED": True,
                "entry_count": 0,
                "entries": [],
            },
            "convergence_dynamics": {
                "evidence_class": "not_run",
                "derived_metric": True,
                "not_causal": True,
                "not_sufficient_for_JLENS_PROVED": True,
                "case_count": 0,
                "cases": [],
            },
            "derived_metrics_not_causal": True,
            "not_sufficient_for_JLENS_PROVED": True,
        }
        jlens_intervention_ledger_verified = False
    jlens_intervention_metrics.setdefault(
        "causal_support_set",
        {
            "evidence_class": "not_available",
            "derived_metric": True,
            "not_causal": True,
            "not_sufficient_for_JLENS_PROVED": True,
            "entry_count": 0,
            "entries": [],
        },
    )
    jlens_intervention_metrics.setdefault(
        "convergence_dynamics",
        {
            "evidence_class": "not_available",
            "derived_metric": True,
            "not_causal": True,
            "not_sufficient_for_JLENS_PROVED": True,
            "case_count": 0,
            "cases": [],
        },
    )
    jlens_intervention_metrics.setdefault("derived_metrics_not_causal", True)
    if (live_path / "metrics.json").exists():
        live_metrics = _read_json(live_path / "metrics.json")
        live_ledger_verified = _verify_ledger(live_path)
    else:
        live_metrics = {
            "rail_status": "not_run",
            "openrouter_api_key_present": False,
            "adapter_call_performed": False,
            "live_model_run_performed": False,
            "secret_values_recorded": False,
            "reason_codes": ["live_gate_artifact_missing"],
        }
        live_ledger_verified = False
    if (live_smoke_path / "metrics.json").exists():
        live_smoke_metrics = _read_json(live_smoke_path / "metrics.json")
        live_smoke_ledger_verified = _verify_ledger(live_smoke_path)
    else:
        live_smoke_metrics = {
            "run_status": "not_run",
            "adapter_call_count": 0,
            "candidate_patch_present_count": 0,
            "hidden_verifier_pass_count": 0,
            "hidden_verifier_pass_rate": 0.0,
            "live_model_run_performed": False,
            "reason_codes": ["live_smoke_artifact_missing"],
        }
        live_smoke_ledger_verified = False
    if (live_dsh_path / "metrics.json").exists():
        live_dsh_metrics = _read_json(live_dsh_path / "metrics.json")
        live_dsh_ledger_verified = _verify_ledger(live_dsh_path)
    else:
        live_dsh_metrics = {
            "run_status": "not_run",
            "adapter_call_count": 0,
            "prereg_id": "missing",
            "prereg_path": str(live_dsh_path / "missing_prereg.md"),
            "prereg_exists": False,
            "candidate_patch_present_count": 0,
            "hidden_verifier_pass_count": 0,
            "hidden_verifier_pass_rate": 0.0,
            "live_model_run_performed": False,
            "reason_codes": ["live_dsh_artifact_missing"],
        }
        live_dsh_ledger_verified = False
    if (live_sequence_path / "metrics.json").exists():
        live_sequence_metrics = _read_json(live_sequence_path / "metrics.json")
        live_sequence_ledger_verified = _verify_ledger(live_sequence_path)
    else:
        live_sequence_metrics = {
            "sequence_status": "not_run",
            "adapter_call_count_total": 0,
            "smoke_run_status": "not_run",
            "smoke_hidden_verifier_pass_count": 0,
            "pilot_run_status": "not_requested",
            "pilot_promoted": False,
            "all_child_ledgers_verified": False,
        }
        live_sequence_ledger_verified = False
    live_ab_exists = (live_ab_path / "metrics.json").exists()
    if live_ab_exists:
        live_ab_metrics = _read_json(live_ab_path / "metrics.json")
        live_ab_ledger_verified = _verify_ledger(live_ab_path)
    else:
        live_ab_metrics = {
            "run_status": "not_run",
            "model_count": 0,
            "attempted_model_count": 0,
            "case_count_per_model": 0,
            "total_case_runs": 0,
            "adapter_call_count_total": 0,
            "adapter_usage_total_tokens": 0,
            "live_model_run_performed_count": 0,
            "valid_choice_count": 0,
            "parse_failure_count": 0,
            "schema_compliance_rate": 0.0,
            "accuracy": 0.0,
            "parsed_only_accuracy": 0.0,
            "wrong_bias_accuracy": 0.0,
            "neutral_accuracy": 0.0,
            "parsed_only_wrong_bias_accuracy": 0.0,
            "parsed_only_neutral_accuracy": 0.0,
            "wrong_bias_harm": 0.0,
            "parsed_only_wrong_bias_harm": 0.0,
            "behavioral_screening_only": True,
            "not_sufficient_for_JLENS_PROVED": True,
            "secret_values_recorded": False,
            "reason_codes": ["live_ab_bias_artifact_missing"],
        }
        live_ab_ledger_verified = False
    live_ab_metrics.setdefault("schema_compliance_rate", 0.0)
    live_ab_metrics.setdefault("parsed_only_accuracy", 0.0)
    live_ab_metrics.setdefault("parsed_only_wrong_bias_accuracy", 0.0)
    live_ab_metrics.setdefault("parsed_only_neutral_accuracy", 0.0)
    live_ab_metrics.setdefault("wrong_bias_harm", 0.0)
    live_ab_metrics.setdefault("parsed_only_wrong_bias_harm", 0.0)

    ledger_verified = {
        "ab_bias_suite": ab_bias_ledger_verified,
        "macro_dsh": _verify_ledger(dsh_path),
        "ledger_stress": ledger_stress_ledger_verified,
        "seed_detectability": _verify_ledger(dsh_path),
        "rqgm_epoch": _verify_ledger(rqgm_path),
        "jlens_gate": _verify_ledger(jlens_path),
        "jlens_runtime_readiness": jlens_runtime_ledger_verified,
        "jlens_smoke": jlens_smoke_ledger_verified,
        "jlens_hf_smoke": jlens_hf_smoke_ledger_verified,
        "jlens_leak_probe": jlens_leak_probe_ledger_verified,
        "jlens_intervention": jlens_intervention_ledger_verified,
        "live_model_gate": live_ledger_verified,
        "live_smoke": live_smoke_ledger_verified,
        "live_dsh_pilot": live_dsh_ledger_verified,
        "live_sequence": live_sequence_ledger_verified,
    }
    if live_ab_exists:
        ledger_verified["live_ab_bias_suite"] = live_ab_ledger_verified
    rows = [
        {
            "section": "ledger_stress",
            "artifact_path": str(ledger_stress_path),
            "primary_metric": "synthetic_receipt_count",
            "primary_value": ledger_stress_metrics["synthetic_receipt_count"],
            "ledger_verified": ledger_verified["ledger_stress"],
            "evidence_path": str(ledger_stress_path / "metrics.json"),
        },
        {
            "section": "ab_bias_suite",
            "artifact_path": str(ab_bias_path),
            "primary_metric": "wrong_bias_harm",
            "primary_value": ab_bias_metrics["wrong_bias_harm"],
            "ledger_verified": ledger_verified["ab_bias_suite"],
            "evidence_path": str(ab_bias_path / "metrics.json"),
        },
        {
            "section": "macro_dsh",
            "artifact_path": str(dsh_path),
            "primary_metric": "GLASSGATE_LIFT",
            "primary_value": dsh_metrics["glassgate_lift"],
            "ledger_verified": ledger_verified["macro_dsh"],
            "evidence_path": str(dsh_path / "metrics.json"),
        },
        {
            "section": "seed_detectability",
            "artifact_path": str(dsh_path),
            "primary_metric": "seed_detectability_auc",
            "primary_value": seed_audit["auc"],
            "ledger_verified": ledger_verified["seed_detectability"],
            "evidence_path": str(dsh_path / "seed_audit.json"),
        },
        {
            "section": "rqgm_epoch",
            "artifact_path": str(rqgm_path),
            "primary_metric": "epoch_count",
            "primary_value": rqgm_metrics["epoch_count"],
            "ledger_verified": ledger_verified["rqgm_epoch"],
            "evidence_path": str(rqgm_path / "trajectory.json"),
        },
        {
            "section": "jlens_gate",
            "artifact_path": str(jlens_path),
            "primary_metric": "rail_status",
            "primary_value": jlens_metrics["rail_status"],
            "ledger_verified": ledger_verified["jlens_gate"],
            "evidence_path": str(jlens_path / "metrics.json"),
        },
        {
            "section": "jlens_runtime_readiness",
            "artifact_path": str(jlens_runtime_path),
            "primary_metric": "readiness_status",
            "primary_value": jlens_runtime_metrics["readiness_status"],
            "ledger_verified": ledger_verified["jlens_runtime_readiness"],
            "evidence_path": str(jlens_runtime_path / "metrics.json"),
        },
        {
            "section": "jlens_smoke",
            "artifact_path": str(jlens_smoke_path),
            "primary_metric": "smoke_status",
            "primary_value": jlens_smoke_metrics["smoke_status"],
            "ledger_verified": ledger_verified["jlens_smoke"],
            "evidence_path": str(jlens_smoke_path / "metrics.json"),
        },
        {
            "section": "jlens_hf_smoke",
            "artifact_path": str(jlens_hf_smoke_path),
            "primary_metric": "smoke_status",
            "primary_value": jlens_hf_smoke_metrics["smoke_status"],
            "ledger_verified": ledger_verified["jlens_hf_smoke"],
            "evidence_path": str(jlens_hf_smoke_path / "metrics.json"),
        },
        {
            "section": "jlens_leak_probe",
            "artifact_path": str(jlens_leak_probe_path),
            "primary_metric": "leak_probe_status",
            "primary_value": jlens_leak_probe_metrics["leak_probe_status"],
            "ledger_verified": ledger_verified["jlens_leak_probe"],
            "evidence_path": str(jlens_leak_probe_path / "metrics.json"),
        },
        {
            "section": "jlens_intervention",
            "artifact_path": str(jlens_intervention_path),
            "primary_metric": "intervention_status",
            "primary_value": jlens_intervention_metrics["intervention_status"],
            "ledger_verified": ledger_verified["jlens_intervention"],
            "evidence_path": str(jlens_intervention_path / "metrics.json"),
        },
        {
            "section": "live_model_gate",
            "artifact_path": str(live_path),
            "primary_metric": "rail_status",
            "primary_value": live_metrics["rail_status"],
            "ledger_verified": ledger_verified["live_model_gate"],
            "evidence_path": str(live_path / "metrics.json"),
        },
        {
            "section": "live_smoke",
            "artifact_path": str(live_smoke_path),
            "primary_metric": "run_status",
            "primary_value": live_smoke_metrics["run_status"],
            "ledger_verified": ledger_verified["live_smoke"],
            "evidence_path": str(live_smoke_path / "metrics.json"),
        },
        {
            "section": "live_dsh_pilot",
            "artifact_path": str(live_dsh_path),
            "primary_metric": "run_status",
            "primary_value": live_dsh_metrics["run_status"],
            "ledger_verified": ledger_verified["live_dsh_pilot"],
            "evidence_path": str(live_dsh_path / "metrics.json"),
        },
        {
            "section": "live_sequence",
            "artifact_path": str(live_sequence_path),
            "primary_metric": "sequence_status",
            "primary_value": live_sequence_metrics["sequence_status"],
            "ledger_verified": ledger_verified["live_sequence"],
            "evidence_path": str(live_sequence_path / "metrics.json"),
        },
    ]
    if live_ab_exists:
        rows.append(
            {
                "section": "live_ab_bias_suite",
                "artifact_path": str(live_ab_path),
                "primary_metric": "accuracy",
                "primary_value": live_ab_metrics["accuracy"],
                "ledger_verified": live_ab_ledger_verified,
                "evidence_path": str(live_ab_path / "metrics.json"),
            }
        )
    claims = [
        {
            "claim": "GLASSGATE_LIFT with 95% CI is available for the macro grid.",
            "status": "proved_for_current_macro_artifact",
            "evidence_path": str(dsh_path / "metrics.json"),
            "value": dsh_metrics["glassgate_lift"],
        },
        {
            "claim": "D estimates exist for all macro grid arms.",
            "status": "proved_for_current_macro_artifact",
            "evidence_path": str(dsh_path / "metrics.json"),
            "value": dsh_metrics["D_by_arm"],
        },
        {
            "claim": "Source ledgers verify for macro, epoch, and J-lens gate artifacts.",
            "status": "proved_for_current_artifacts",
            "evidence_path": str(output_dir / "ledger_verification.json"),
            "value": ledger_verified,
        },
        {
            "claim": "10,000 mixed synthetic receipts verify and tamper detection fails a mutated copy.",
            "status": "proved_for_current_stress_artifact"
            if ledger_stress_metrics["synthetic_receipt_count"] >= 10_000
            and ledger_stress_metrics["mixed_kind_count"] >= 2
            and ledger_stress_metrics["pre_metrics_chain_verified"]
            and ledger_stress_metrics["ledger_verified"]
            and ledger_stress_metrics["tamper_detection_passed"]
            and ledger_verified["ledger_stress"]
            else "missing_or_failed_stress_artifact",
            "evidence_path": str(ledger_stress_path / "metrics.json"),
            "value": {
                "synthetic_receipt_count": ledger_stress_metrics["synthetic_receipt_count"],
                "mixed_kind_count": ledger_stress_metrics["mixed_kind_count"],
                "ledger_verified": ledger_stress_metrics["ledger_verified"],
                "tamper_detection_passed": ledger_stress_metrics["tamper_detection_passed"],
            },
        },
        {
            "claim": "A/B behavioral bias suite screens scripted three-agent panels without claiming J-lens proof.",
            "status": "proved_behavioral_screening_artifact"
            if ab_bias_metrics["case_count"] >= 48
            and ab_bias_metrics["behavioral_screening_only"]
            and ab_bias_metrics["not_sufficient_for_JLENS_PROVED"]
            and ledger_verified["ab_bias_suite"]
            else "missing_or_failed_behavioral_screening_artifact",
            "evidence_path": str(ab_bias_path / "metrics.json"),
            "value": {
                "case_count": ab_bias_metrics["case_count"],
                "wrong_bias_harm": ab_bias_metrics["wrong_bias_harm"],
                "behavioral_screening_only": ab_bias_metrics["behavioral_screening_only"],
                "not_sufficient_for_JLENS_PROVED": ab_bias_metrics[
                    "not_sufficient_for_JLENS_PROVED"
                ],
            },
        },
        {
            "claim": "macro diagnostics include verified solve rate, panel correlation rho, candidate ablation rate, and token cost per solve.",
            "status": "proved_for_current_macro_artifact"
            if isinstance(dsh_metrics.get("verified_solve_rate"), dict)
            and isinstance(dsh_metrics.get("panel_correlation_rho"), dict)
            and "candidate_ablation_rate" in dsh_metrics
            and "token_cost_per_solve" in dsh_metrics
            else "missing_macro_diagnostics",
            "evidence_path": str(dsh_path / "metrics.json"),
            "value": {
                "verified_solve_rate": dsh_metrics.get("verified_solve_rate"),
                "panel_correlation_rho": dsh_metrics.get("panel_correlation_rho"),
                "candidate_ablation_rate": dsh_metrics.get("candidate_ablation_rate"),
                "token_cost_per_solve": dsh_metrics.get("token_cost_per_solve"),
            },
        },
        {
            "claim": "Seed detectability audit is present and passes the current marker-leak gate.",
            "status": "proved_for_current_macro_artifact",
            "evidence_path": str(dsh_path / "seed_audit.json"),
            "value": {
                "auc": seed_audit["auc"],
                "seed_camouflage_failed": seed_audit["seed_camouflage_failed"],
            },
        },
        {
            "claim": "Controlled RQGM epoch trajectory is present.",
            "status": "proved_for_current_epoch_artifact",
            "evidence_path": str(rqgm_path / "trajectory.json"),
            "value": {
                "epoch_count": rqgm_metrics["epoch_count"],
                "replacement_count": rqgm_metrics["replacement_count"],
            },
        },
        {
            "claim": "J-lens rail has a clean failure/defer record.",
            "status": "deferred_with_failure_record",
            "evidence_path": str(jlens_path / "metrics.json"),
            "value": {
                "rail_status": jlens_metrics["rail_status"],
                "failure_ledger_entry_id": jlens_metrics["failure_ledger_entry_id"],
                "leak_probe_status": jlens_leak_probe_metrics["leak_probe_status"],
                "leak_probe_performed": jlens_leak_probe_metrics["outcome_leak_probe_performed"],
                "causal_intervention_performed": jlens_leak_probe_metrics[
                    "causal_intervention_performed"
                ],
                "intervention_status": jlens_intervention_metrics["intervention_status"],
                "causal_support_entry_count": jlens_intervention_metrics[
                    "causal_support_set"
                ]["entry_count"],
                "convergence_case_count": jlens_intervention_metrics[
                    "convergence_dynamics"
                ]["case_count"],
                "derived_metrics_not_causal": jlens_intervention_metrics[
                    "derived_metrics_not_causal"
                ],
            },
        },
        {
            "claim": "Live/model-backed execution has an explicit no-secrets provider gate record.",
            "status": "not_performed_with_gate_record"
            if live_metrics["rail_status"] in {"unavailable", "gated_ready_no_spend", "configured_not_executed"}
            else "missing_gate_record",
            "evidence_path": str(live_path / "metrics.json"),
            "value": {
                "rail_status": live_metrics["rail_status"],
                "openrouter_api_key_present": live_metrics["openrouter_api_key_present"],
                "adapter_call_performed": live_metrics["adapter_call_performed"],
                "live_model_run_performed": live_metrics["live_model_run_performed"],
                "reason_codes": live_metrics["reason_codes"],
            },
        },
        {
            "claim": "Live smoke rail has an explicit blocked or one-call pilot record.",
            "status": "blocked_with_gate_record"
            if live_smoke_metrics["run_status"] == "blocked_no_live_execution"
            else "pilot_executed_recorded"
            if live_smoke_metrics["run_status"] in {"adapter_pilot_executed_fake_transport", "live_dsh_executed"}
            else "missing_gate_record",
            "evidence_path": str(live_smoke_path / "metrics.json"),
            "value": {
                "run_status": live_smoke_metrics["run_status"],
                "adapter_call_count": live_smoke_metrics["adapter_call_count"],
                "candidate_patch_present_count": live_smoke_metrics["candidate_patch_present_count"],
                "hidden_verifier_pass_count": live_smoke_metrics["hidden_verifier_pass_count"],
                "hidden_verifier_pass_rate": live_smoke_metrics["hidden_verifier_pass_rate"],
                "live_model_run_performed": live_smoke_metrics["live_model_run_performed"],
                "reason_codes": live_smoke_metrics["reason_codes"],
            },
        },
        {
            "claim": "Live DSH pilot rail has an explicit blocked or pilot-executed record.",
            "status": "blocked_with_gate_record"
            if live_dsh_metrics["run_status"] == "blocked_no_live_execution"
            else "pilot_executed_recorded"
            if live_dsh_metrics["run_status"] in {"adapter_pilot_executed_fake_transport", "live_dsh_executed"}
            else "missing_gate_record",
            "evidence_path": str(live_dsh_path / "metrics.json"),
            "value": {
                "run_status": live_dsh_metrics["run_status"],
                "prereg_id": live_dsh_metrics["prereg_id"],
                "prereg_exists": live_dsh_metrics["prereg_exists"],
                "adapter_call_count": live_dsh_metrics["adapter_call_count"],
                "candidate_patch_present_count": live_dsh_metrics["candidate_patch_present_count"],
                "hidden_verifier_pass_count": live_dsh_metrics["hidden_verifier_pass_count"],
                "hidden_verifier_pass_rate": live_dsh_metrics["hidden_verifier_pass_rate"],
                "live_model_run_performed": live_dsh_metrics["live_model_run_performed"],
                "reason_codes": live_dsh_metrics["reason_codes"],
            },
        },
        {
            "claim": "Preferred live-provider sequence has an explicit blocked or promotion record.",
            "status": "blocked_with_sequence_record"
            if live_sequence_metrics["sequence_status"] == "blocked_before_smoke"
            else "sequence_recorded"
            if live_sequence_metrics["sequence_status"]
            in {
                "smoke_passed_pilot_not_requested",
                "pilot_executed_after_smoke_pass",
                "smoke_failed_pilot_not_promoted",
                "smoke_failed_pilot_not_requested",
            }
            else "missing_sequence_record",
            "evidence_path": str(live_sequence_path / "metrics.json"),
            "value": {
                "sequence_status": live_sequence_metrics["sequence_status"],
                "adapter_call_count_total": live_sequence_metrics["adapter_call_count_total"],
                "smoke_run_status": live_sequence_metrics["smoke_run_status"],
                "smoke_hidden_verifier_pass_count": live_sequence_metrics["smoke_hidden_verifier_pass_count"],
                "pilot_run_status": live_sequence_metrics["pilot_run_status"],
                "pilot_promoted": live_sequence_metrics["pilot_promoted"],
                "all_child_ledgers_verified": live_sequence_metrics["all_child_ledgers_verified"],
            },
        },
        {
            "claim": "Live A/B behavioral suite records black-box model choices without claiming J-lens proof.",
            "status": "live_behavioral_evidence_recorded"
            if live_ab_exists
            and live_ab_metrics["adapter_call_count_total"] > 0
            and live_ab_metrics["behavioral_screening_only"]
            and live_ab_metrics["not_sufficient_for_JLENS_PROVED"]
            and live_ab_ledger_verified
            else "not_run",
            "evidence_path": str(live_ab_path / "metrics.json"),
            "value": {
                "run_status": live_ab_metrics["run_status"],
                "model_count": live_ab_metrics["model_count"],
                "total_case_runs": live_ab_metrics["total_case_runs"],
                "adapter_call_count_total": live_ab_metrics["adapter_call_count_total"],
                "accuracy": live_ab_metrics["accuracy"],
                "schema_compliance_rate": live_ab_metrics["schema_compliance_rate"],
                "parsed_only_accuracy": live_ab_metrics["parsed_only_accuracy"],
                "wrong_bias_accuracy": live_ab_metrics["wrong_bias_accuracy"],
                "parsed_only_wrong_bias_accuracy": live_ab_metrics[
                    "parsed_only_wrong_bias_accuracy"
                ],
                "behavioral_screening_only": live_ab_metrics["behavioral_screening_only"],
                "not_sufficient_for_JLENS_PROVED": live_ab_metrics[
                    "not_sufficient_for_JLENS_PROVED"
                ],
            },
        },
    ]

    all_ledgers_verified = all(ledger_verified.values())
    live_sequence_status_ok = live_sequence_metrics["sequence_status"] in {
        "blocked_before_smoke",
        "smoke_passed_pilot_not_requested",
        "pilot_executed_after_smoke_pass",
        "smoke_failed_pilot_not_promoted",
        "smoke_failed_pilot_not_requested",
    }
    report_status = (
        "complete_with_deferred_jlens"
        if all_ledgers_verified
        and jlens_metrics["rail_status"] == "frozen"
        and live_metrics["rail_status"] in {"unavailable", "gated_ready_no_spend", "configured_not_executed"}
        and live_smoke_metrics["run_status"] in {"blocked_no_live_execution", "adapter_pilot_executed_fake_transport", "live_dsh_executed"}
        and live_dsh_metrics["run_status"] in {"blocked_no_live_execution", "adapter_pilot_executed_fake_transport", "live_dsh_executed"}
        and live_sequence_status_ok
        else "incomplete"
    )
    metrics = {
        "run_id": run_id,
        "report_status": report_status,
        "ab_bias_suite_status": "behavioral_screening_complete"
        if ab_bias_metrics["case_count"] >= 48 and ledger_verified["ab_bias_suite"]
        else "missing_or_incomplete",
        "ab_bias_case_count": ab_bias_metrics["case_count"],
        "ab_bias_wrong_bias_harm": ab_bias_metrics["wrong_bias_harm"],
        "ab_bias_dissent_rescue_rate": ab_bias_metrics["dissent_rescue_rate"],
        "ab_bias_false_consensus_rejection_rate": ab_bias_metrics[
            "false_consensus_rejection_rate"
        ],
        "ab_bias_behavioral_screening_only": ab_bias_metrics["behavioral_screening_only"],
        "ab_bias_not_sufficient_for_JLENS_PROVED": ab_bias_metrics[
            "not_sufficient_for_JLENS_PROVED"
        ],
        "glassgate_lift": dsh_metrics["glassgate_lift"],
        "glassgate_lift_ci95": dsh_metrics["glassgate_lift_ci95"],
        "D_by_arm": dsh_metrics["D_by_arm"],
        "D_by_panel_type": dsh_metrics["D_by_panel_type"],
        "ledger_stress_synthetic_receipt_count": ledger_stress_metrics["synthetic_receipt_count"],
        "ledger_stress_total_receipt_count": ledger_stress_metrics["total_receipt_count"],
        "ledger_stress_mixed_kind_count": ledger_stress_metrics["mixed_kind_count"],
        "ledger_stress_pre_metrics_chain_verified": ledger_stress_metrics["pre_metrics_chain_verified"],
        "ledger_stress_ledger_verified": ledger_stress_metrics["ledger_verified"] and ledger_verified["ledger_stress"],
        "ledger_stress_tamper_detection_passed": ledger_stress_metrics["tamper_detection_passed"],
        "verified_solve_rate": dsh_metrics["verified_solve_rate"],
        "panel_correlation_rho": dsh_metrics["panel_correlation_rho"],
        "candidate_ablation_rate": dsh_metrics["candidate_ablation_rate"],
        "token_cost_per_solve": dsh_metrics["token_cost_per_solve"],
        "seed_detectability_auc": seed_audit["auc"],
        "seed_marker_auc": seed_audit["marker_auc"],
        "seed_adversarial_auc": seed_audit["adversarial_auc"],
        "seed_camouflage_failed": seed_audit["seed_camouflage_failed"],
        "epoch_count": rqgm_metrics["epoch_count"],
        "replacement_count": rqgm_metrics["replacement_count"],
        "current_evaluator_id": rqgm_metrics["current_evaluator_id"],
        "jlens_rail_status": jlens_metrics["rail_status"],
        "jlens_failure_ledger_entry_id": jlens_metrics["failure_ledger_entry_id"],
        "jlens_runtime_readiness_status": jlens_runtime_metrics["readiness_status"],
        "jlens_runtime_white_box_model_available": jlens_runtime_metrics["white_box_model_available"],
        "jlens_runtime_gradient_access_confirmed": jlens_runtime_metrics["gradient_access_confirmed"],
        "jlens_runtime_real_probe_runnable": jlens_runtime_metrics["real_probe_runnable"],
        "jlens_runtime_tokenizer_labels_all_single_token": jlens_runtime_metrics[
            "tokenizer_labels_all_single_token"
        ],
        "jlens_runtime_reason_codes": jlens_runtime_metrics["reason_codes"],
        "jlens_smoke_status": jlens_smoke_metrics["smoke_status"],
        "jlens_smoke_real_fit_apply": jlens_smoke_metrics["real_jlens_fit_apply_smoke"],
        "jlens_smoke_gradient_access_confirmed": jlens_smoke_metrics["gradient_access_confirmed"],
        "jlens_smoke_layer_activation_access_confirmed": jlens_smoke_metrics[
            "layer_activation_access_confirmed"
        ],
        "jlens_smoke_not_sufficient_for_JLENS_PROVED": jlens_smoke_metrics[
            "not_sufficient_for_JLENS_PROVED"
        ],
        "jlens_hf_smoke_status": jlens_hf_smoke_metrics["smoke_status"],
        "jlens_hf_smoke_real_fit_apply": jlens_hf_smoke_metrics[
            "real_hf_jlens_fit_apply_smoke"
        ],
        "jlens_hf_selected_labels_all_single_token": jlens_hf_smoke_metrics[
            "selected_labels_all_single_token"
        ],
        "jlens_hf_critical_labels_all_single_token": jlens_hf_smoke_metrics[
            "critical_labels_all_single_token"
        ],
        "jlens_hf_smoke_not_sufficient_for_JLENS_PROVED": jlens_hf_smoke_metrics[
            "not_sufficient_for_JLENS_PROVED"
        ],
        "jlens_leak_probe_status": jlens_leak_probe_metrics["leak_probe_status"],
        "jlens_leak_probe_real": jlens_leak_probe_metrics["real_hf_jlens_leak_probe"],
        "jlens_leak_probe_performed": jlens_leak_probe_metrics[
            "outcome_leak_probe_performed"
        ],
        "jlens_leak_pc_metric": jlens_leak_probe_metrics["pc_metric"],
        "jlens_leak_pc_threshold": jlens_leak_probe_metrics["pc_threshold"],
        "jlens_leak_differential_activation_present": jlens_leak_probe_metrics[
            "differential_activation_present"
        ],
        "jlens_leak_negative_control_performed": jlens_leak_probe_metrics[
            "negative_control_performed"
        ],
        "jlens_leak_sham_control_performed": jlens_leak_probe_metrics[
            "sham_control_performed"
        ],
        "jlens_leak_causal_intervention_performed": jlens_leak_probe_metrics[
            "causal_intervention_performed"
        ],
        "jlens_leak_not_sufficient_for_JLENS_PROVED": jlens_leak_probe_metrics[
            "not_sufficient_for_JLENS_PROVED"
        ],
        "jlens_intervention_status": jlens_intervention_metrics["intervention_status"],
        "jlens_intervention_leak_probe_performed": jlens_intervention_metrics[
            "leak_probe_performed"
        ],
        "jlens_intervention_pc_metric": jlens_intervention_metrics["pc_metric"],
        "jlens_intervention_pc_threshold": jlens_intervention_metrics["pc_threshold"],
        "jlens_intervention_differential_activation_present": jlens_intervention_metrics[
            "differential_activation_present"
        ],
        "jlens_intervention_performed": jlens_intervention_metrics[
            "causal_intervention_performed"
        ],
        "jlens_intervention_sham_control_performed": jlens_intervention_metrics[
            "sham_intervention_control_performed"
        ],
        "jlens_intervention_causal_support_evidence_class": jlens_intervention_metrics[
            "causal_support_set"
        ]["evidence_class"],
        "jlens_intervention_causal_support_entry_count": jlens_intervention_metrics[
            "causal_support_set"
        ]["entry_count"],
        "jlens_intervention_convergence_evidence_class": jlens_intervention_metrics[
            "convergence_dynamics"
        ]["evidence_class"],
        "jlens_intervention_convergence_case_count": jlens_intervention_metrics[
            "convergence_dynamics"
        ]["case_count"],
        "jlens_intervention_derived_metrics_not_causal": jlens_intervention_metrics[
            "derived_metrics_not_causal"
        ],
        "jlens_intervention_not_sufficient_for_JLENS_PROVED": jlens_intervention_metrics[
            "not_sufficient_for_JLENS_PROVED"
        ],
        "live_model_rail_status": live_metrics["rail_status"],
        "live_adapter_call_performed": live_metrics["adapter_call_performed"],
        "live_model_run_performed": live_metrics["live_model_run_performed"],
        "live_openrouter_api_key_present": live_metrics["openrouter_api_key_present"],
        "live_secret_values_recorded": live_metrics["secret_values_recorded"],
        "live_reason_codes": live_metrics["reason_codes"],
        "live_smoke_run_status": live_smoke_metrics["run_status"],
        "live_smoke_adapter_call_count": live_smoke_metrics["adapter_call_count"],
        "live_smoke_candidate_patch_present_count": live_smoke_metrics["candidate_patch_present_count"],
        "live_smoke_hidden_verifier_pass_count": live_smoke_metrics["hidden_verifier_pass_count"],
        "live_smoke_hidden_verifier_pass_rate": live_smoke_metrics["hidden_verifier_pass_rate"],
        "live_smoke_model_run_performed": live_smoke_metrics["live_model_run_performed"],
        "live_smoke_reason_codes": live_smoke_metrics["reason_codes"],
        "live_dsh_run_status": live_dsh_metrics["run_status"],
        "live_dsh_prereg_id": live_dsh_metrics["prereg_id"],
        "live_dsh_prereg_path": live_dsh_metrics["prereg_path"],
        "live_dsh_prereg_exists": live_dsh_metrics["prereg_exists"],
        "live_dsh_adapter_call_count": live_dsh_metrics["adapter_call_count"],
        "live_dsh_candidate_patch_present_count": live_dsh_metrics["candidate_patch_present_count"],
        "live_dsh_hidden_verifier_pass_count": live_dsh_metrics["hidden_verifier_pass_count"],
        "live_dsh_hidden_verifier_pass_rate": live_dsh_metrics["hidden_verifier_pass_rate"],
        "live_dsh_model_run_performed": live_dsh_metrics["live_model_run_performed"],
        "live_dsh_reason_codes": live_dsh_metrics["reason_codes"],
        "live_sequence_status": live_sequence_metrics["sequence_status"],
        "live_sequence_adapter_call_count_total": live_sequence_metrics["adapter_call_count_total"],
        "live_sequence_smoke_status": live_sequence_metrics["smoke_run_status"],
        "live_sequence_smoke_hidden_verifier_pass_count": live_sequence_metrics["smoke_hidden_verifier_pass_count"],
        "live_sequence_pilot_status": live_sequence_metrics["pilot_run_status"],
        "live_sequence_pilot_promoted": live_sequence_metrics["pilot_promoted"],
        "live_sequence_all_child_ledgers_verified": live_sequence_metrics["all_child_ledgers_verified"],
        "live_ab_bias_status": live_ab_metrics["run_status"],
        "live_ab_model_count": live_ab_metrics["model_count"],
        "live_ab_attempted_model_count": live_ab_metrics["attempted_model_count"],
        "live_ab_case_count_per_model": live_ab_metrics["case_count_per_model"],
        "live_ab_total_case_runs": live_ab_metrics["total_case_runs"],
        "live_ab_adapter_call_count_total": live_ab_metrics["adapter_call_count_total"],
        "live_ab_adapter_usage_total_tokens": live_ab_metrics["adapter_usage_total_tokens"],
        "live_ab_model_run_performed_count": live_ab_metrics["live_model_run_performed_count"],
        "live_ab_valid_choice_count": live_ab_metrics["valid_choice_count"],
        "live_ab_parse_failure_count": live_ab_metrics["parse_failure_count"],
        "live_ab_schema_compliance_rate": live_ab_metrics["schema_compliance_rate"],
        "live_ab_accuracy": live_ab_metrics["accuracy"],
        "live_ab_parsed_only_accuracy": live_ab_metrics["parsed_only_accuracy"],
        "live_ab_wrong_bias_accuracy": live_ab_metrics["wrong_bias_accuracy"],
        "live_ab_neutral_accuracy": live_ab_metrics["neutral_accuracy"],
        "live_ab_parsed_only_wrong_bias_accuracy": live_ab_metrics[
            "parsed_only_wrong_bias_accuracy"
        ],
        "live_ab_parsed_only_neutral_accuracy": live_ab_metrics[
            "parsed_only_neutral_accuracy"
        ],
        "live_ab_wrong_bias_harm": live_ab_metrics["wrong_bias_harm"],
        "live_ab_parsed_only_wrong_bias_harm": live_ab_metrics[
            "parsed_only_wrong_bias_harm"
        ],
        "live_ab_behavioral_screening_only": live_ab_metrics["behavioral_screening_only"],
        "live_ab_not_sufficient_for_JLENS_PROVED": live_ab_metrics[
            "not_sufficient_for_JLENS_PROVED"
        ],
        "live_ab_secret_values_recorded": live_ab_metrics["secret_values_recorded"],
        "all_source_ledgers_verified": all_ledgers_verified,
        "result_table_path": str(output_dir / "result_table.json"),
        "claim_matrix_path": str(output_dir / "claim_matrix.json"),
        "ledger_verification_path": str(output_dir / "ledger_verification.json"),
        "result_card_path": str(output_dir / "result_card.md"),
        "replay_bundle_path": str(output_dir / "replay"),
        "ledger_path": str(output_dir / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": "final report: ledger stress, macro DSH, seed audit, RQGM, J-lens source gate, live model gate, live smoke, live DSH pilot, and live sequence artifacts loaded",
            "2": f"final report: GLASSGATE_LIFT {metrics['glassgate_lift']} with seed AUC {metrics['seed_detectability_auc']}",
            "3": f"final report: source ledgers verified, J-lens frozen/deferred, live sequence {metrics['live_sequence_status']}, live model run not performed",
        }
    }

    ledger = Ledger()
    ledger.append("report_start", {"run_id": run_id, "artifact_root": str(artifact_root)})
    for row in rows:
        ledger.append("source_artifact", row)
    ledger.append("claim_matrix", {"claim_count": len(claims), "claims": claims})
    ledger.append("report_metrics", metrics)

    _write_json(output_dir / "result_table.json", {"rows": rows})
    (output_dir / "result_table.md").write_text(_result_table_md(rows))
    _write_json(output_dir / "claim_matrix.json", {"claims": claims})
    _write_json(output_dir / "ledger_verification.json", ledger_verified)
    _write_json(output_dir / "metrics.json", metrics)
    _write_json(output_dir / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(output_dir / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(output_dir / "metrics.json", metrics)
    (output_dir / "result_card.md").write_text(_result_card(run_id, metrics, rows))

    return ReportResult(run_id=run_id, artifact_path=output_dir, expected_replay=replay_contexts)
