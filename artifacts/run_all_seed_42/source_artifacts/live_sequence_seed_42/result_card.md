# Result Card: live_sequence_seed_42

Run type: live provider execution sequence

## Decision

Sequence status: blocked_before_smoke
Adapter calls total: 0
Smoke status: blocked_no_live_execution
Smoke hidden verifier pass count: 0
Pilot requested: False
Pilot promoted: False
Pilot status: not_requested

The sequence is blocked before smoke; no adapter call was made.

This sequence does not compute or claim GLASSGATE_LIFT.

## Child artifacts

| Artifact | Path | Ledger verified |
|---|---|---:|
| live_model_gate | artifacts/run_all_seed_42/source_artifacts/live_sequence_seed_42/source_artifacts/live_gate_seed_42 | True |
| live_smoke | artifacts/run_all_seed_42/source_artifacts/live_sequence_seed_42/source_artifacts/live_smoke_seed_42 | True |

## Replay

Ledger: artifacts/run_all_seed_42/source_artifacts/live_sequence_seed_42/ledger.jsonl
Replay bundle: artifacts/run_all_seed_42/source_artifacts/live_sequence_seed_42/replay
Tamper check: pass
