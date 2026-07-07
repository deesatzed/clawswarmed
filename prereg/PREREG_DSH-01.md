# PREREG_DSH-01

## Claim

C-MACRO-1: scarce protected broadcast preserves correct minority signal better
than abundant transcript, random admission, and naive top-k scarcity.

## Conditions

- panel_type: `correlated_shared_context`, `partitioned_disjoint_shards`
- workspace_arm: `abundant`, `random`, `scarce_naive_topk`,
  `scarce_protected`
- seed_condition: `correct_minority`, `incorrect_minority`, `none`

## Primary Metric

`GLASSGATE_LIFT`.

## Kill Criterion

If scarce protected fails to beat all three controls on D, or
`GLASSGATE_LIFT <= 0`, the governance thesis is unsupported for this run.

## Seed

42 unless overridden in the run artifact.

