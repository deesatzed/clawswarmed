# Live DSH Pilot

Date: 2026-07-07

## Purpose

`run-live-dsh` is the first command path for model-backed DSH panel work. It
uses the same panel types, workspace arms, and seed conditions as the macro DSH
rail, but it is a pilot rail. It does not produce `GLASSGATE_LIFT` or replace
the deterministic macro result.

## Command

```bash
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
prereg_id = PREREG_LIVE-01
prereg_exists = true
adapter_call_count = 0
candidate_patch_present_count = 0
hidden_verifier_pass_count = 0
hidden_verifier_pass_rate = 0.0
live_model_run_performed = false
```

The test suite exercises the 24-cell pilot through fake transport so request
construction, adapter call accounting, replay, ledger verification, and
secret-exclusion behavior are covered without external API calls.

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
