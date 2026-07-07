# Live Model Gate

Date: 2026-07-07

## Purpose

The Glass Gate instrument must not blur deterministic evidence with live model
claims. `run-live-gate` creates a replayable provider-readiness artifact before
any live model call exists.

The gate records:

- whether `OPENROUTER_API_KEY` is present by name;
- whether `OPENROUTER_MODEL` is present by name;
- whether API spend was authorized;
- whether a network probe ran;
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
credentials, spend authorization, and a tested model adapter are introduced.
