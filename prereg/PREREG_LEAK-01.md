# PREREG_LEAK-01

## Claim

C-MICRO-1: outcome leakage installs a verdict-direction representation in the
gatekeeper before evidence is processed.

## Primary Metric

Premature convergence PC from a white-box gatekeeper probe.

## Kill Criterion

If the probe shows no differential activation, freeze the J-lens rail and
continue macro/RQGM rails.

## Source Gate

Do not implement a real probe until the exact paper, repository, or method
source is located and cited.

## Candidate Seed-Camouflage Subgate

Before treating any macro result as credible, run a seed-detectability audit on
public candidate fields. Seed labels may exist in hidden verification fields,
but candidate IDs and public presentation fields must not expose markers such
as `correct_minority`, `incorrect_minority`, `minority`, `seeded`, or `seed`.

Pass criterion for the current deterministic audit:

- `seed_detectability_auc` remains within 0.1 of chance.
- `seed_camouflage_failed = false`.
- `leak_markers_found = []`.
