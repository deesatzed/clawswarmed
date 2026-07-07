# Live Model Gate

Date: 2026-07-07

## Purpose

The Glass Gate instrument must not blur deterministic evidence with live model
claims. `run-live-gate` creates a replayable provider-readiness artifact and
contains the first gated OpenRouter adapter contract.

The gate records:

- whether `OPENROUTER_API_KEY` is present by name;
- whether `OPENROUTER_MODEL` is present by name;
- whether API spend was authorized;
- whether live execution was explicitly requested;
- whether a network probe ran;
- whether the adapter call path was exercised;
- whether a live model run was performed;
- whether any secret values were recorded.

Secret values are never written to `metrics.json`, `provider_status.json`,
`result_card.md`, or `ledger.jsonl`.

## Command

```bash
python3 -m broadcast_alpha run-live-gate --seed 42
```

Optional env-file inspection:

```bash
python3 -m broadcast_alpha run-live-gate --seed 42 --env-file /path/to/.env
```

This parses simple `KEY=value` lines and records only presence booleans.

Adapter execution requires all of the following:

- `OPENROUTER_API_KEY` is present in the process or reviewed env file;
- `OPENROUTER_MODEL` is present or `--model` is passed;
- `--authorize-api-spend` is passed;
- `--execute-live` is passed.

Example shape:

```bash
python3 -m broadcast_alpha run-live-gate --seed 42 \
  --env-file /path/to/.env \
  --model openrouter/model-slug \
  --authorize-api-spend \
  --execute-live
```

That command is intentionally not part of the checked-in verification run. The
tests exercise the adapter through a fake transport, proving request
construction, response sanitization, ledgering, replay, and secret exclusion
without making an external call.

## Current Artifact

```text
artifacts/live_gate_seed_42/
```

Files:

- `metrics.json`
- `provider_status.json`
- `result_card.md`
- `ledger.jsonl`
- `replay/contexts.json`

## Boundary

The current gate is not a live model-backed panel run. It is the safety and
provenance layer that makes the remaining live-model gap explicit before API
credentials and spend authorization are used for a real panel experiment.
