# Result Card: final_report_seed_42

Run type: consolidated Broadcast-alpha / Glass Gate report

## One-number demo

GLASSGATE_LIFT = 0.4 [95% CI: 0.15, 0.55]

## D by arm

| Arm | D |
|---|---:|
| abundant | 0.15 |
| random | 0.216667 |
| scarce_naive_topk | 0.116667 |
| scarce_protected | 0.616667 |

## Required evidence

- ledger_stress: synthetic_receipt_count = 10000
- ab_bias_suite: wrong_bias_harm = 0.625
- macro_dsh: GLASSGATE_LIFT = 0.4
- seed_detectability: seed_detectability_auc = 0.5
- rqgm_epoch: epoch_count = 5
- jlens_gate: rail_status = frozen
- jlens_runtime_readiness: readiness_status = blocked_missing_dependencies
- jlens_smoke: smoke_status = passed
- jlens_hf_smoke: smoke_status = passed
- jlens_leak_probe: leak_probe_status = passed
- jlens_intervention: intervention_status = blocked_no_differential_signal
- live_model_gate: rail_status = unavailable
- live_smoke: run_status = blocked_no_live_execution
- live_dsh_pilot: run_status = blocked_no_live_execution
- live_sequence: sequence_status = blocked_before_smoke
- live_ab_bias_suite: accuracy = 0.571429

## 10k ledger stress

Synthetic stress receipts: 10000
Mixed receipt kinds: 8
Tamper detection passed: True

## Macro diagnostics

Verified solve rate: {'abundant': 0.605556, 'random': 0.627778, 'scarce_naive_topk': 0.594444, 'scarce_protected': 0.761111}
Panel correlation rho: {'correlated_shared_context': 0.82, 'partitioned_disjoint_shards': 0.28}
Candidate ablation rate: 0.297222
Token cost per solve: None

## Seed detectability audit

Seed detectability AUC: 0.5
Adversarial token AUC: 0.5
Camouflage failed: False

## RQGM epoch trajectory

Epoch count: 5
Replacement count: 3
Current evaluator: eval_gate_v5

## A/B behavioral bias

A/B suite status: behavioral_screening_complete
A/B cases: 64
A/B wrong-bias harm: 0.625
A/B dissent rescue rate: 1.0
A/B false consensus rejection rate: 1.0
A/B behavioral screening only: True
A/B sufficient for J-lens proof: False

## J-lens rail

J-lens rail frozen: True
Failure ledger entry: JLENS-FREEZE-001
Runtime readiness: blocked_missing_dependencies
Runtime reason codes: ['torch_missing', 'transformers_missing', 'jacobian_lens_reference_missing', 'tokenizer_label_check_incomplete']
White-box model available: False
Tokenizer labels verified: False
Fit/apply smoke: passed
Fit/apply smoke real: True
Fit/apply smoke sufficient for proof: False
HF smoke: passed
HF smoke real: True
HF selected labels single-token: True
HF critical labels single-token: False
Leak probe: passed
Leak probe performed: True
Leak PC metric: 0.07183928849796455
Leak differential activation: False
Leak causal intervention: False
Intervention gate: blocked_no_differential_signal
Intervention performed: False
Intervention sham control: False
Intervention derived metrics non-causal: True
Causal support set entries: 2
Convergence dynamics cases: 2

## Live model rail

Live model rail status: unavailable
Adapter call performed: False
Live model run performed: False
OpenRouter API key present by name: False
No secret values recorded: True

## Live A/B behavioral

Live A/B status: live_ab_executed
Live A/B models: 7
Live A/B case runs: 28
Live A/B adapter calls: 28
Live A/B accuracy: 0.571429
Live A/B wrong-bias accuracy: 0.571429
Live A/B parse failures: 12
Live A/B behavioral only: True

## Live smoke

Live smoke status: blocked_no_live_execution
Live smoke adapter calls: 0
Live smoke hidden verifier pass count: 0
Live smoke hidden verifier pass rate: 0.0

## Live sequence

Live sequence status: blocked_before_smoke
Live sequence adapter calls: 0
Live sequence smoke status: blocked_no_live_execution
Live sequence pilot status: not_requested
Live sequence pilot promoted: False

## Live DSH pilot

Live DSH pilot status: blocked_no_live_execution
Live DSH prereg: PREREG_LIVE-01
Live DSH adapter calls: 0
Live DSH hidden verifier pass count: 0
Live DSH hidden verifier pass rate: 0.0

## Replay

Ledger: artifacts/final_report_seed_42/ledger.jsonl
Replay bundle: artifacts/final_report_seed_42/replay
Tamper check: pass
