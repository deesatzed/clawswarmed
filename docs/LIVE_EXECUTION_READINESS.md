# Live Execution Readiness

Date: 2026-07-07

## Purpose

`prepare-live-smoke` is a no-spend inspection command for the first real
provider-backed smoke. It exports the planned one-call request shape before any
API call is authorized.

The command does not call OpenRouter, does not run a network probe, and does
not record secret values.

## Command

```bash
python3 -m broadcast_alpha prepare-live-smoke --prereg prereg/PREREG_LIVE-01.md --seed 42
```

With a reviewed env file and explicit model:

```bash
python3 -m broadcast_alpha prepare-live-smoke --prereg prereg/PREREG_LIVE-01.md --seed 42 --env-file /path/to/.env --model openrouter/model-slug
```

## Current Artifact

```text
artifacts/live_readiness_seed_42/
```

Files:

- `request_preview.json`
- `gate_checklist.json`
- `metrics.json`
- `result_card.md`
- `ledger.jsonl`
- `replay/contexts.json`

## Current Status

```text
readiness_status = blocked_missing_configuration
adapter_call_count = 0
live_model_run_performed = false
secret_values_recorded = false
hidden_tests_included = false
```

## Boundary

The request preview is not execution evidence. It redacts `Authorization`,
includes only public task data, and excludes hidden verifier cases and seeded
patches.

The first real call still requires explicit user authorization for provider
spend and the execution command must include `--authorize-api-spend` and
`--execute-live`.
