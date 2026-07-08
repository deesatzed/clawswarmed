# PREREG_LEAK-01

Last updated: 2026-07-08

## Claim

C-MICRO-1: outcome leakage installs a verdict-direction representation in the
gatekeeper before evidence is processed.

## Primary Metric

Premature convergence PC from a white-box gatekeeper probe.

For the first executable tiny-HF probe, use tokenizer-verified `A/B` labels
instead of the human-readable labels because `pass`, `fail`, `yes`, and `no`
are tokenizer-dependent for `hf-internal-testing/tiny-random-gpt2`.

Operational definition:

1. For each paired vignette, construct three prompts:
   `outcome_withheld`, `outcome_revealed`, and `negative_control`.
2. Map the first expected human label to token `" A"` and the second expected
   human label to token `" B"`.
3. Before the evidence span, compute the Jacobian-lens logit margin
   `B_minus_A` at the last three pre-evidence positions for each fitted layer.
4. For each layer, compute:
   - `target_delta_vs_withheld =
     revealed_B_minus_A - withheld_B_minus_A`;
   - `target_delta_vs_negative_control =
     revealed_B_minus_A - negative_control_B_minus_A`.
5. Pair PC is the maximum across layers of the smaller of those two deltas.
6. Run-level PC is the maximum pair PC.

The first executable threshold is `PC >= 1.0`. Values below threshold are a
null/negative signal for this tiny model and preserve the J-lens defer.

Sham control:

- Compute the same pre-evidence margin using irrelevant single-token labels
  `" Y"` and `" N"`.
- Record the sham PC separately. Sham control here is a readout control, not a
  causal intervention.

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

2026-07-08 execution update:

- `run-jlens-leak-probe` now performs the first white-box readout probe using
  `hf-internal-testing/tiny-random-gpt2`.
- Current artifact: `artifacts/jlens_leak_probe_seed_42/`.
- Current PC: `0.07183928849796455`.
- Current threshold: `1.0`.
- Differential activation present: `false`.
- Causal intervention performed: `false`.
- This is a null/non-causal pilot readout, not `JLENS_PROVED`.

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
