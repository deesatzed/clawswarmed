# PREREG_LIVE-01

## Claim

C-LIVEPREREG-1: `run-live-dsh` is a gated live-model DSH pilot rail with a
committed preregistration record before any provider-backed output can be used
as evidence.

## Command

```bash
python3 -m broadcast_alpha run-live-dsh --prereg prereg/PREREG_LIVE-01.md --seed 42 --tasks-per-cell 1
```

## Conditions

- panel_type: `correlated_shared_context`, `partitioned_disjoint_shards`
- workspace_arm: `abundant`, `random`, `scarce_naive_topk`,
  `scarce_protected`
- seed_condition: `correct_minority`, `incorrect_minority`, `none`
- default task count: 1 task per cell for the pilot rail
- planned cells: 24

## Execution Gates

The default run must produce `blocked_no_live_execution`.

Provider-backed execution requires all of:

- `OPENROUTER_API_KEY`;
- `OPENROUTER_MODEL` or `--model`;
- `--authorize-api-spend`;
- `--execute-live`;
- this preregistration file present at run time.

No API call, network probe, or provider spend is allowed by default.

## Structured Output

Adapter responses should put the candidate patch in the first message content as
JSON:

```json
{"patch": "x + 2", "rationale": "repair add"}
```

The pilot must parse the patch and run it through the hidden verifier before
reporting candidate outcome metrics.

## Primary Pilot Metrics

- `run_status`
- `adapter_call_count`
- `candidate_patch_present_count`
- `candidate_patch_parse_failure_count`
- `hidden_verifier_pass_count`
- `hidden_verifier_pass_rate`
- `live_model_run_performed`

## Evidence Boundary

No GLASSGATE_LIFT claim may be made from:

- a blocked run;
- a fake-transport run;
- a run with `prereg_exists = false`;
- a run that records secret values;
- a run without replay and ledger verification.

The deterministic macro DSH rail remains the source of current
`GLASSGATE_LIFT` until a separately preregistered live macro grid is approved
and executed.

## Kill / Defer Criteria

Defer or reject live DSH evidence if:

- the provider key or model is missing;
- API spend was not explicitly authorized;
- `--execute-live` was not supplied;
- this preregistration file is missing;
- any artifact records a secret value;
- adapter responses cannot be parsed into verifier-backed candidate outcomes;
- ledger verification or replay fails.

