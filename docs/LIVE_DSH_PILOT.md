# Live DSH Pilot

Date: 2026-07-07

## Purpose

`run-live-dsh` is the first command path for model-backed DSH panel work. It
uses the same panel types, workspace arms, and seed conditions as the macro DSH
rail, but it is a pilot rail. It does not produce `GLASSGATE_LIFT` or replace
the deterministic macro result.

`run-live-smoke` is the safer first provider-backed step. It uses the same
request, verifier, ledger, replay, and no-secret machinery, but hard-limits the
run to one DSH cell and one task.

`run-live-sequence` is the intended one-command provider path. It records
provider readiness, runs smoke only when all live gates are explicitly opened,
and promotes to the 24-cell pilot only when `--include-dsh-pilot` is supplied
and smoke has a verifier-backed pass.

## Command

```bash
python3 -m broadcast_alpha run-live-sequence --prereg prereg/PREREG_LIVE-01.md --seed 42
python3 -m broadcast_alpha run-live-smoke --prereg prereg/PREREG_LIVE-01.md --seed 42
python3 -m broadcast_alpha run-live-dsh --prereg prereg/PREREG_LIVE-01.md --seed 42 --tasks-per-cell 1
```

Real provider-backed execution requires:

- committed preregistration at `prereg/PREREG_LIVE-01.md`;
- `OPENROUTER_API_KEY`;
- `OPENROUTER_MODEL` or `--model`;
- `--authorize-api-spend`;
- `--execute-live`.

## Current Artifact

```text
artifacts/live_sequence_seed_42/
artifacts/live_smoke_seed_42/
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
live_smoke.run_status = blocked_no_live_execution
live_smoke.cell_limit = 1
live_smoke.planned_task_runs = 1
live_smoke.adapter_call_count = 0
live_sequence.sequence_status = blocked_before_smoke
live_sequence.adapter_call_count_total = 0
run_status = blocked_no_live_execution
prereg_id = PREREG_LIVE-01
prereg_exists = true
adapter_call_count = 0
candidate_patch_present_count = 0
hidden_verifier_pass_count = 0
hidden_verifier_pass_rate = 0.0
live_model_run_performed = false
```

The test suite exercises the one-cell smoke and the 24-cell pilot through fake
transport so request construction, adapter call accounting, replay, ledger
verification, hidden verifier outcomes, and secret-exclusion behavior are
covered without external API calls.

## Structured Patch Format

Adapter responses can provide a candidate patch in the first message content as
JSON:

```json
{"patch": "x + 2", "rationale": "repair add"}
```

When a patch is present, the pilot runs it through the same hidden verifier used
by the deterministic codebug task bank and records:

- `candidate_patch_parse_status`
- `hidden_verifier_passed`
- `hidden_verifier_total`
- `hidden_verifier_failures`

These verifier-backed outcomes make the live rail ready for a bounded provider
pilot, but fake-transport outcomes are not live model evidence.

## Evidence Boundary

Blocked and fake-transport runs do not produce a live `GLASSGATE_LIFT` claim.
The prereg file is recorded in metrics and the run-start receipt so later
provider-backed pilots can be audited against the committed run contract.
