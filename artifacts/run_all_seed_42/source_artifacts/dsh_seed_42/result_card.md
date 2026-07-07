# Result Card: dsh_seed_42

Prereg: PREREG_DSH-01
Seed: 42
Task suite: synthetic_codebug
Panel types: correlated_shared_context, partitioned_disjoint_shards
Arms: abundant, random, scarce_naive_topk, scarce_protected

## One-number demo

GLASSGATE_LIFT = 0.4 [95% CI: 0.15, 0.55]

## D by arm

| Arm | D | 95% CI | Verified solve rate | Token cost/solve |
|---|---:|---:|---:|---:|
| abundant | 0.15 | n/a | 0.605556 | n/a |
| random | 0.216667 | n/a | 0.627778 | n/a |
| scarce_naive_topk | 0.116667 | n/a | 0.594444 | n/a |
| scarce_protected | 0.616667 | n/a | 0.761111 | n/a |

## Interpretation

24-cell DSH grid over deterministic codebug tasks with executable hidden tests. This is not an LLM-token run.

## Seed detectability audit

Seed detectability AUC: 0.5
Adversarial token AUC: 0.5
Camouflage failed: False
Audit path: artifacts/run_all_seed_42/source_artifacts/dsh_seed_42/seed_audit.json


## Replay

Ledger: artifacts/run_all_seed_42/source_artifacts/dsh_seed_42/ledger.jsonl
Replay bundle: artifacts/run_all_seed_42/source_artifacts/dsh_seed_42/replay
Tamper check: pass

## Failure ledger updates

None.
