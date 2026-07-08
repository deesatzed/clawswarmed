# Result Card: jlens_hf_smoke_seed_42

Run type: Hugging Face J-lens fit/apply smoke

## Verdict

Smoke status: passed
Real HF J-lens fit/apply smoke: True
Selected labels all single-token: True
Critical labels all single-token: False
Gradient access confirmed: True
Layer activation access confirmed: True
Causal intervention performed: False

This smoke uses a tiny Hugging Face decoder and proves the HF adapter can fit
and apply a Jacobian lens locally. It is not an outcome-leak probe and is not
sufficient for `JLENS_PROVED`.

## Replay

Ledger: artifacts/run_all_seed_42/source_artifacts/jlens_hf_smoke_seed_42/ledger.jsonl
Replay bundle: artifacts/run_all_seed_42/source_artifacts/jlens_hf_smoke_seed_42/replay
Tamper check: pass
