# Live DSH Pilot

Date: 2026-07-07

## Purpose

`run-live-dsh` is the first command path for model-backed DSH panel work. It
uses the same panel types, workspace arms, and seed conditions as the macro DSH
rail, but it is a pilot rail. It does not produce `GLASSGATE_LIFT` or replace
the deterministic macro result.

## Command

```bash
python3 -m broadcast_alpha run-live-dsh --seed 42 --tasks-per-cell 1
```

Real provider-backed execution requires:

- `OPENROUTER_API_KEY`;
- `OPENROUTER_MODEL` or `--model`;
- `--authorize-api-spend`;
- `--execute-live`.

## Current Artifact

```text
artifacts/live_dsh_seed_42/
```

Files:

- `metrics.json`
- `task_runs.json`
- `result_card.md`
- `ledger.jsonl`
- `replay/contexts.json`

## Current Status

The checked-in artifact is blocked by design:

```text
run_status = blocked_no_live_execution
adapter_call_count = 0
live_model_run_performed = false
```

The test suite exercises the 24-cell pilot through fake transport so request
construction, adapter call accounting, replay, ledger verification, and
secret-exclusion behavior are covered without external API calls.
