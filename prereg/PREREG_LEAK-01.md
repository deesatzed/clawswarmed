# PREREG_LEAK-01

Last updated: 2026-07-08

## Claim

C-MICRO-1: outcome leakage installs a verdict-direction representation in the
gatekeeper before evidence is processed.

## Primary Metric

Premature convergence PC from a white-box gatekeeper probe.

## Kill Criterion

If the probe shows no differential activation, freeze the J-lens rail and
continue macro/RQGM rails.

## Source Gate

The exact source blocker is resolved:

- `https://github.com/anthropics/jacobian-lens`
- `https://transformer-circuits.pub/2026/workspace/index.html`

Do not implement or claim a real probe until a white-box model runtime, fitted
Jacobian lens, tokenizer-specific label check, and causal intervention controls
are configured.

The checked-in no-code/manual seed packet is:

- `prereg/jlens_vignette_packet_01.json`

Manual viewer observations must use
`docs/JLENS_MANUAL_SANITY_TEMPLATE.md` and cannot satisfy this preregistration.

## Candidate Seed-Camouflage Subgate

Before treating any macro result as credible, run a seed-detectability audit on
public candidate fields. Seed labels may exist in hidden verification fields,
but candidate IDs and public presentation fields must not expose markers such
as `correct_minority`, `incorrect_minority`, `minority`, `seeded`, or `seed`.

Pass criterion for the current deterministic audit:

- `seed_detectability_auc` remains within 0.1 of chance.
- `seed_camouflage_failed = false`.
- `leak_markers_found = []`.
