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

- macro_dsh: GLASSGATE_LIFT = 0.4
- seed_detectability: seed_detectability_auc = 0.5
- rqgm_epoch: epoch_count = 5
- jlens_gate: rail_status = frozen
- live_model_gate: rail_status = unavailable
- live_dsh_pilot: run_status = blocked_no_live_execution

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

## Live model rail

Live model rail status: unavailable
Adapter call performed: False
Live model run performed: False
OpenRouter API key present by name: False
No secret values recorded: True

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
