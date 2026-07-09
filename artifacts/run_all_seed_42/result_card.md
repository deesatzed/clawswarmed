# Result Card: run_all_seed_42

Run type: unattended Broadcast-alpha / Glass Gate bundle

## One-number demo

GLASSGATE_LIFT = 0.4 [95% CI: 0.15, 0.55]

## Summary

Run status: complete_with_deferred_jlens
Seed detectability AUC: 0.5
Adversarial token AUC: 0.5
Ledger stress receipts: 10000
Ledger stress tamper detection: True
Candidate ablation rate: 0.297222
Token cost per solve: None
RQGM epochs: 5
J-lens rail: frozen
Live model rail: unavailable
Adapter call performed: False
Live model run performed: False
Live smoke: blocked_no_live_execution
Live smoke verifier pass rate: 0.0
Live DSH pilot: blocked_no_live_execution
Live DSH prereg: PREREG_LIVE-01
Live DSH verifier pass rate: 0.0
Live sequence: blocked_before_smoke
Live sequence adapter calls: 0
Live A/B behavioral: blocked_no_live_execution
Live A/B adapter calls: 0
Live A/B schema compliance rate: 0.0
Live A/B parsed-only accuracy: 0.0

## Child artifacts

| Artifact | Path | Ledger verified |
|---|---|---:|
| ab_bias_suite | artifacts/run_all_seed_42/source_artifacts/ab_bias_suite_seed_42 | True |
| ledger_stress | artifacts/run_all_seed_42/source_artifacts/ledger_stress_seed_42 | True |
| synthetic | artifacts/run_all_seed_42/source_artifacts/synthetic_seed_42 | True |
| dsh | artifacts/run_all_seed_42/source_artifacts/dsh_seed_42 | True |
| rqgm | artifacts/run_all_seed_42/source_artifacts/rqgm_seed_42 | True |
| jlens_gate | artifacts/run_all_seed_42/source_artifacts/jlens_gate_seed_42 | True |
| jlens_runtime_readiness | artifacts/run_all_seed_42/source_artifacts/jlens_runtime_readiness_seed_42 | True |
| jlens_smoke | artifacts/run_all_seed_42/source_artifacts/jlens_smoke_seed_42 | True |
| jlens_hf_smoke | artifacts/run_all_seed_42/source_artifacts/jlens_hf_smoke_seed_42 | True |
| jlens_leak_probe | artifacts/run_all_seed_42/source_artifacts/jlens_leak_probe_seed_42 | True |
| jlens_intervention | artifacts/run_all_seed_42/source_artifacts/jlens_intervention_seed_42 | True |
| live_model_gate | artifacts/run_all_seed_42/source_artifacts/live_gate_seed_42 | True |
| live_smoke | artifacts/run_all_seed_42/source_artifacts/live_smoke_seed_42 | True |
| live_dsh_pilot | artifacts/run_all_seed_42/source_artifacts/live_dsh_seed_42 | True |
| live_sequence | artifacts/run_all_seed_42/source_artifacts/live_sequence_seed_42 | True |
| live_ab_bias_suite | artifacts/run_all_seed_42/source_artifacts/live_ab_bias_suite_seed_42 | True |
| final_report | artifacts/run_all_seed_42/final_report | True |

## Replay

Ledger: artifacts/run_all_seed_42/ledger.jsonl
Replay bundle: artifacts/run_all_seed_42/replay
Tamper check: pass
