# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add a `prepare-live-smoke` readiness rail that exports a sanitized preview of
the exact one-call live smoke request and its execution gates without making a
network call or recording secrets.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to the remaining live/model-backed requirement
by making the first real provider call inspectable before it is authorized. The
user should be able to see the planned smoke request, hidden-verifier boundary,
required gates, and exact follow-up command without exposing credentials or
spending API budget.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `broadcast_alpha/live_readiness.py` | New readiness rail with sanitized request preview, gate checklist, metrics, replay, result card, and ledger. | Could accidentally include secrets or hidden tests. |
| `broadcast_alpha/cli.py` | Add `prepare-live-smoke` command. | CLI could be confused with execution. |
| `tests/test_broadcast_alpha.py` | Add TDD coverage for sanitized request preview, zero adapter calls, CLI replay, and ledger verification. | Tests must check no secret and no hidden-test leakage. |
| `docs/LIVE_EXECUTION_READINESS.md`, `README.md`, `docs/LIVE_DSH_PILOT.md` | Document the readiness preview and its boundary. | Docs could imply readiness equals execution. |
| `artifacts/live_readiness_seed_42/` | Generated current no-spend readiness artifact. | Generated ledger churn. |
| Root `DECISIONS.md`, `PROGRESS.md` | Record workflow/progress update. | Root is not Git-backed. |

## Existing Patterns To Follow

- Rail functions return dataclasses with `run_id`, `artifact_path`, and
  `expected_replay`.
- Every rail writes `metrics.json`, `result_card.md`, `ledger.jsonl`, and
  `replay/contexts.json`.
- `run-live-smoke` uses `live_dsh._task_request()` to build the one-cell smoke
  request. Reuse that shape instead of creating a second prompt path.
- Live rails record env var presence by name only and never record secret
  values.
- Tests use fake/local transports for network-protected behavior.

## Assumptions

- No real OpenRouter request is allowed in this pass.
- The readiness rail can read env presence and model values, but it must not
  record API key values.
- The request preview may include the public codebug prompt and panel/arm/seed
  metadata, but it must not include hidden tests.
- The command reads local task/prereg/env metadata and does not run experiments.

## Non-Goals For This Pass

- Do not run a live model-backed call.
- Do not call OpenRouter or any external API.
- Do not add non-stdlib dependencies.
- Do not change macro, RQGM, live, report, run-all, or audit outputs except
  adding the readiness artifact.
- Do not mark `GOAL_GLASSGATE.md` complete.
- Do not reopen the J-lens rail.

## Step-by-Step Plan

1. Write failing tests for API and CLI readiness artifacts.
2. Implement `broadcast_alpha.live_readiness.prepare_live_smoke`.
3. Add CLI command.
4. Document the readiness artifact and generate
   `artifacts/live_readiness_seed_42/`.
5. Run verification and commit/push.

## Acceptance Criteria

- `prepare-live-smoke` writes `artifacts/live_readiness_seed_42/`.
- Artifact includes `request_preview.json`, `gate_checklist.json`,
  `metrics.json`, `result_card.md`, `ledger.jsonl`, and
  `replay/contexts.json`.
- Request preview uses the live smoke task request shape, redacts
  authorization, and includes no API key value.
- Request preview includes no hidden-test expected values.
- Metrics record zero adapter calls and no live model run.
- Gate checklist names all required gates before execution.
- Existing tests pass.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m py_compile claswarmed/*.py`
- `python3 -m broadcast_alpha prepare-live-smoke --artifact-root artifacts --prereg prereg/PREREG_LIVE-01.md --seed 42`
- `python3 -m broadcast_alpha summarize artifacts/live_readiness_seed_42`
- `python3 -m broadcast_alpha export-ledger artifacts/live_readiness_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/live_readiness_seed_42 --agent agent_1 --step 3`
- `git diff --check`
- secret scan for provider key patterns in code/docs/artifacts
- `git status --short --branch`

## Rollback Plan

Revert the readiness rail commit and remove `artifacts/live_readiness_seed_42/`.

## Risks

| Risk | Mitigation |
|---|---|
| Secret leakage | Redact `Authorization`, never write API key values, and scan artifacts before commit. |
| Hidden-test leakage | Build request preview from public task data only and test that hidden expected values are absent. |
| Preview mistaken for execution | Metrics hard-code `adapter_call_count = 0`, `live_model_run_performed = false`, and result card states no API call was made. |
| Prompt drift | Reuse `live_dsh._task_request()` to preserve the live smoke request shape. |

## Proceed / Block Decision

Proceed. The pass does not require credentials, external spend, protected repo
mutation, or production deployment.
