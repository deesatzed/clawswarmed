# PREREG_AB-01

## Claim Under Test

The A/B Bias Challenge Suite is a behavioral screening rail. It tests whether
controlled three-agent panels can expose cases where a judge follows evidence
or follows social/context bias.

This prereg does not claim J-lens, J-space, activation, gradient, or causal
evidence.

## Rival Hypotheses

### A. Bias-Active Hypothesis

Wrong social/context cues reduce evidence-following accuracy, especially when
the correct claim is outvoted or when all visible agent claims are wrong.

### B. Bias-Null Hypothesis

Wrong social/context cues do not reduce accuracy once evidence is explicit.
Observed failures are ordinary task difficulty or case-quality problems rather
than bias.

## Panel Compositions

- `two_correct_one_wrong`
- `one_correct_two_wrong`
- `three_correct`
- `zero_correct`

## Bias Conditions

- `neutral`
- `wrong_bias`
- `correct_bias`
- `irrelevant_bias`

Bias types may include majority, authority, reputation, outcome-leak, and
format/confidence cues.

## Task Families

Use evidence-contained tasks first:

- logic/rule-following;
- code patch pass/fail;
- table/data interpretation;
- agent-judge promotion.

Do not use open-world knowledge in v1 unless the facts needed to answer are
inside the prompt.

## Primary Metrics

- `neutral_baseline_accuracy`
- `wrong_bias_accuracy`
- `correct_bias_accuracy`
- `irrelevant_bias_accuracy`
- `wrong_bias_harm`
- `correct_cue_help`
- `dissent_rescue_rate`
- `correct_majority_acceptance_rate`
- `false_consensus_rejection_rate`
- `all_correct_acceptance_rate`
- `discriminating_case_count`

## Reference Judges

The first run uses scripted no-network judges:

- `evidence_oracle`
- `majority_biased`
- `authority_biased`
- `format_biased`

These judges are controls for case and metric behavior. They are not model
results.

## No-J-lens Overclaim Rule

Every artifact from this prereg must label itself:

- `evidence_class = behavioral_screening`
- `behavioral_screening_only = true`
- `not_jlens_evidence = true`
- `not_activation_measurement = true`
- `not_causal = true`
- `not_sufficient_for_JLENS_PROVED = true`

Black-box model runs, if added later, remain behavioral only. A later J-lens
run requires a white-box model with gradient/layer access and a separate
mechanistic prereg/proof gate.

## Promotion Rule

Only case families with repeatable behavioral separation should be promoted to
larger model or white-box J-lens work.
