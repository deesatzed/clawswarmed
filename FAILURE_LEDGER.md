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

- The exact named source from the handoff was not verified in the current
  source lookup.
- No configured white-box gatekeeper model with gradient/layer access is
  available in this repository/runtime.
- Timing or readout alone is insufficient for the Glass Gate causal claim.

Decision: do not implement or claim a real J-lens probe. Continue macro DSH
and RQGM rails. Optional bridge and mechanistic rails remain deferred.

Evidence:

- `artifacts/jlens_gate_seed_42/sources.json` records searched queries and
  verified adjacent sources.
- `artifacts/jlens_gate_seed_42/metrics.json` sets `rail_status = frozen`.
- `artifacts/jlens_gate_seed_42/ledger.jsonl` includes a
  `jlens_gate_decision` receipt.
