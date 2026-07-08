# Result Card: final_report

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
- macro_dsh: GLASSGATE_LIFT = 0.4
- seed_detectability: seed_detectability_auc = 0.5
- rqgm_epoch: epoch_count = 5
- jlens_gate: rail_status = frozen
- jlens_runtime_readiness: readiness_status = blocked_missing_dependencies
- jlens_smoke: smoke_status = passed
- live_model_gate: rail_status = unavailable
- live_smoke: run_status = blocked_no_live_execution
- live_dsh_pilot: run_status = blocked_no_live_execution
- live_sequence: sequence_status = blocked_before_smoke

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

## Live model rail

Live model rail status: unavailable
Adapter call performed: False
Live model run performed: False
OpenRouter API key present by name: False
No secret values recorded: True

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

Ledger: artifacts/run_all_seed_42/final_report/ledger.jsonl
Replay bundle: artifacts/run_all_seed_42/final_report/replay
Tamper check: pass
