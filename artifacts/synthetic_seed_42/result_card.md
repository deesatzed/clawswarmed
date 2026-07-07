# Result Card: synthetic_seed_42

Prereg: PREREG_DSH-01
Seed: 42
Task suite: synthetic
Panel types: correlated_shared_context, partitioned_disjoint_shards
Arms: abundant, random, scarce_naive_topk, scarce_protected

## One-number demo

GLASSGATE_LIFT = 0.3 [95% CI: 0.2, 0.4]

## D by arm

| Arm | D | 95% CI | Verified solve rate | Token cost/solve |
|---|---:|---:|---:|---:|
| abundant | 0.09999999999999998 | n/a | 0.7 | n/a |
| random | 0.2 | n/a | 0.7 | n/a |
| scarce_naive_topk | 0.0 | n/a | 0.7 | n/a |
| scarce_protected | 0.5 | n/a | 0.7 | n/a |

## Interpretation

Synthetic deterministic harness output. This is not a live macro claim.

## Replay

Ledger: artifacts/synthetic_seed_42/ledger.jsonl
Replay bundle: artifacts/synthetic_seed_42/replay
Tamper check: pass

## Failure ledger updates

None.
