# PREREG_CAUSAL-01

## Claim

C-MICRO-2: early verdict representation is causal, not cosmetic.

## Primary Metric

Change in final verdict or D after ablation, swap, or suppression versus sham
control.

## Kill Criterion

If intervention does not move final verdicts or D, hindsight scores are treated
as noise for this rail.

## Pre-Intervention Signal Gate

Do not run a causal intervention if the current preregistered leak probe has no
meaningful differential activation. For the first tiny-HF probe, this means:

- `pc_metric < pc_threshold`; or
- `differential_activation_present = false`.

In that case, write a replayable intervention gate artifact with status
`blocked_no_differential_signal` and keep the J-lens rail frozen.

## 2026-07-08 Execution Update

- Input leak probe: `artifacts/jlens_leak_probe_seed_42/`
- Intervention gate artifact: `artifacts/jlens_intervention_seed_42/`
- Intervention status: `blocked_no_differential_signal`
- PC metric: `0.07183928849796455`
- PC threshold: `1.0`
- Causal intervention performed: `false`
- Sham intervention control performed: `false`
- Derived `causal_support_set` entries: `2`
- Derived `convergence_dynamics` cases: `2`
- Derived metrics are labeled non-causal and cannot satisfy this preregistered
  causal proof requirement.

This is a clean defer/kill record, not a causal result.
