# Result Card: jlens_smoke_seed_42

Run type: J-lens fit/apply smoke

## Verdict

Smoke status: passed
Real J-lens fit/apply smoke: True
Gradient access confirmed: True
Layer activation access confirmed: True
Causal intervention performed: False

This smoke uses the reference repo's CPU-only tiny decoder. It proves that the
local reference implementation can fit and apply a Jacobian lens, but it is not
an outcome-leak probe and is not sufficient for `JLENS_PROVED`.

## Replay

Ledger: artifacts/run_all_seed_42/source_artifacts/jlens_smoke_seed_42/ledger.jsonl
Replay bundle: artifacts/run_all_seed_42/source_artifacts/jlens_smoke_seed_42/replay
Tamper check: pass
