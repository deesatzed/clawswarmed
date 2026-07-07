# Result Card: dsh_seed_42

Prereg: PREREG_DSH-01
Seed: 42
Task suite: synthetic_codebug
Panel types: correlated_shared_context, partitioned_disjoint_shards
Arms: abundant, random, scarce_naive_topk, scarce_protected

## One-number demo

GLASSGATE_LIFT = 0.4 [95% CI: 0.35, 0.45]

## D by arm

| Arm | D | 95% CI | Verified solve rate | Token cost/solve |
|---|---:|---:|---:|---:|
| abundant | 0.15 | n/a | 0.466667 | n/a |
| random | 0.216667 | n/a | 0.483333 | n/a |
| scarce_naive_topk | 0.116667 | n/a | 0.461111 | n/a |
| scarce_protected | 0.616667 | n/a | 0.588889 | n/a |

## Interpretation

24-cell DSH grid over scripted hard-verifier tasks. This is a deterministic macro harness, not an LLM-token run.

## Replay

Ledger: artifacts/dsh_seed_42/ledger.jsonl
Replay bundle: artifacts/dsh_seed_42/replay
Tamper check: pass

## Failure ledger updates

None.
