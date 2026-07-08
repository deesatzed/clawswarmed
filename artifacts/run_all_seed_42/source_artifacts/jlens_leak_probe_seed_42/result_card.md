# Result Card: jlens_leak_probe_seed_42

Run type: Hugging Face J-lens outcome-leak probe

## Verdict

Probe status: passed
Outcome-leak probe performed: True
PC metric: 0.07183928849796455
PC threshold: 1.0
Differential activation present: False
Negative control performed: True
Sham control performed: True
Causal intervention performed: False

This probe records pre-evidence verdict-label readouts from a tiny Hugging Face
decoder using a fitted Jacobian lens. It is not causal and is not sufficient for
`JLENS_PROVED` without a later intervention/sham-control artifact.

## Replay

Ledger: artifacts/run_all_seed_42/source_artifacts/jlens_leak_probe_seed_42/ledger.jsonl
Replay bundle: artifacts/run_all_seed_42/source_artifacts/jlens_leak_probe_seed_42/replay
Tamper check: pass
