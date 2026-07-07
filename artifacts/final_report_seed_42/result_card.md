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

- macro_dsh: GLASSGATE_LIFT = 0.4
- seed_detectability: seed_detectability_auc = 0.5
- rqgm_epoch: epoch_count = 5
- jlens_gate: rail_status = frozen

## Seed detectability audit

Seed detectability AUC: 0.5
Camouflage failed: False

## RQGM epoch trajectory

Epoch count: 5
Replacement count: 3
Current evaluator: eval_gate_v5

## J-lens rail

J-lens rail frozen: True
Failure ledger entry: JLENS-FREEZE-001

## Replay

Ledger: artifacts/final_report_seed_42/ledger.jsonl
Replay bundle: artifacts/final_report_seed_42/replay
Tamper check: pass
