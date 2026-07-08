# FAILURE_LEDGER.md

This ledger records failed assumptions, killed rails, and negative results for
the Broadcast-alpha / Glass Gate instrument. A negative result is acceptable
when it cleanly kills a claim.

## Pre-Seeded Failure Modes

1. Workspace presence is not influence.
2. J-lens timing is not causality.
3. Local-vs-frontier comparisons are invalid unless layer access, finetuning,
   or representation manipulation is the variable.
4. Cross-model agreement is not a ground-truth anchor.
5. Scarcity can suppress dissent.
6. Protected slots can inflate survival circularly; use influence and D.
7. RQGM without an exogenous verifier can Goodhart into mutual hallucination.
8. Seeded candidates must be camouflaged; otherwise gates can learn seed
   format.
9. Tombstone authority, never delete records.
10. Typed JSON is not the post-linguistic A2A thesis.
11. A negative result is not a failure if it kills a claim cleanly.
12. Do not add another explainer before one run exists.

## Entries

### JLENS-FREEZE-001 - J-lens Source/Model Gate Frozen

Status: frozen/deferred
Date: 2026-07-07
Artifact: `artifacts/jlens_gate_seed_42/`

Reason:

- Original 2026-07-07 blocker: the exact named source from the handoff was not
  verified in the current source lookup.
- 2026-07-08 amendment: the exact source is now verified as
  `https://github.com/anthropics/jacobian-lens` and
  `https://transformer-circuits.pub/2026/workspace/index.html`; the rail
  remains frozen for runtime/model/intervention reasons.
- 2026-07-08 amendment: local reference and Hugging Face tiny-model fit/apply
  smokes passed in the external runtime.
- 2026-07-08 amendment: the first tiny-HF outcome-leak readout probe ran at
  `artifacts/jlens_leak_probe_seed_42/`; PC was
  `0.07183928849796455` against threshold `1.0`, so no differential activation
  was detected for this pilot.
- Timing or readout alone is insufficient for the Glass Gate causal claim.
- No causal intervention or causal sham-control artifact exists yet.

Decision: do not claim a prejudgment detector, causal mechanism, bridge rail,
or mechanistic admission result. Continue macro DSH and RQGM rails. Optional
bridge and mechanistic rails remain deferred.

Evidence:

- `artifacts/jlens_gate_seed_42/sources.json` records searched queries,
  verified exact sources, manual sanity surfaces, and verified adjacent
  sources.
- `artifacts/jlens_gate_seed_42/metrics.json` sets `rail_status = frozen`.
- `artifacts/jlens_gate_seed_42/ledger.jsonl` includes a
  `jlens_gate_decision` receipt.
- `artifacts/jlens_leak_probe_seed_42/metrics.json` records
  `outcome_leak_probe_performed = true`,
  `differential_activation_present = false`, and
  `causal_intervention_performed = false`.
