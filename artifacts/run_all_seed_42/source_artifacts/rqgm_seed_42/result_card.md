# Result Card: rqgm_seed_42

Prereg: PREREG_EPOCH-01
Seed: 42
Run type: 5-epoch RQGM controlled evaluator evolution

## Epoch trajectory

| Epoch | Incumbent | Challenger | Replaced | Challenger GLASSGATE_LIFT | Active after |
|---|---|---|---:|---:|---|
| epoch_1 | eval_gate_v0 | eval_gate_v1 | True | 0.343333 | eval_gate_v1 |
| epoch_2 | eval_gate_v1 | eval_gate_v2 | False | 0.358333 | eval_gate_v1 |
| epoch_3 | eval_gate_v1 | eval_gate_v3 | True | 0.413333 | eval_gate_v3 |
| epoch_4 | eval_gate_v3 | eval_gate_v4 | False | 0.443333 | eval_gate_v3 |
| epoch_5 | eval_gate_v3 | eval_gate_v5 | True | 0.473333 | eval_gate_v5 |

## Summary

Epoch count: 5
Replacement count: 3
Final active evaluator: eval_gate_v5
Tombstoned score count: 3
Active J-lens veto: False

## Interpretation

Synthetic macro-safe RQGM run. Evaluator/gate semantics are frozen within each
epoch; challengers are admitted only at epoch boundaries after margin,
seed-camouflage, solve-degradation, and J-lens-veto checks.

## Replay

Ledger: artifacts/run_all_seed_42/source_artifacts/rqgm_seed_42/ledger.jsonl
Replay bundle: artifacts/run_all_seed_42/source_artifacts/rqgm_seed_42/replay
Tamper check: pass

## Failure ledger updates

None.
