# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add a bounded `run-live-smoke` rail that exercises exactly one verifier-backed
DSH task cell when live execution is explicitly authorized. By default it must
write a blocked no-spend artifact, just like the other live rails.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to a real replayable Glass Gate instrument by
creating the safe first step toward model-backed challenger behavior. The full
24-cell live DSH pilot is too broad for a first provider-backed smoke, so this
rail gives one auditable call path with the same preregistration, hidden
verifier, replay, ledger, and no-secret guarantees.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `broadcast_alpha/live_dsh.py` | Support bounded cell selection and smoke run metadata while preserving the default 24-cell pilot. | Could accidentally change the default DSH pilot artifact. |
| `broadcast_alpha/cli.py` | Add `run-live-smoke` with the same live gates and prereg default. | CLI could make a live call too easy. |
| `broadcast_alpha/reporting.py` | Include the live smoke artifact in consolidated report metrics and claims. | Report could overclaim a blocked or fake smoke as live evidence. |
| `broadcast_alpha/orchestrator.py` | Add the live smoke child artifact to `run-all`. | Run-all could become confusing if smoke and DSH pilot are not clearly separated. |
| `tests/test_broadcast_alpha.py` | Add TDD coverage for blocked smoke, fake-transport one-call smoke, CLI artifact creation, report propagation, and run-all propagation. | Tests may duplicate live DSH assertions instead of proving the one-call constraint. |
| `docs/LIVE_DSH_PILOT.md` | Document live smoke as the first provider-backed step. | Docs could overclaim current checked-in evidence. |
| `README.md`, `docs/RUN_ALL.md`, `docs/FINAL_REPORT.md` | Update artifact descriptions with live smoke status. | Drift between docs and artifacts. |
| `artifacts/` | Regenerate live gate, live smoke, live DSH, final report, and run-all artifacts without real credentials. | Ledger churn in generated bundles. |
| Root `DECISIONS.md`, `PROGRESS.md` | Record security/workflow decision and progress. | Root is not Git-backed. |

## Existing Patterns To Follow

- Rail functions return dataclasses with `run_id`, `artifact_path`, and
  `expected_replay`.
- Every rail writes `metrics.json`, `result_card.md`, `ledger.jsonl`, and
  `replay/contexts.json`.
- `run-live-dsh` already plans the 24-cell live DSH pilot and blocks by
  default.
- The live DSH path already records structured patch parsing, hidden verifier
  outcomes, sanitized adapter metadata, replay, and ledger receipts.
- `build-report` and `run-all` already include live gate and live DSH pilot
  children.
- Tests use fake/local transports for network-protected behavior.

## Assumptions

- No real OpenRouter request is allowed in this pass.
- `PREREG_LIVE-01.md` can govern the live smoke rail because it already defines
  the pilot evidence boundary and forbids `GLASSGATE_LIFT` claims from smoke,
  blocked, fake-transport, or missing-prereg runs.
- The live smoke rail should run the first deterministic DSH cell only:
  `correlated_shared_context / abundant / correct_minority`, one task.
- Future real smoke execution must still require provider key, model,
  `--authorize-api-spend`, `--execute-live`, and the prereg file.

## Non-Goals For This Pass

- Do not run a live model-backed panel or smoke call.
- Do not call OpenRouter or any external API.
- Do not add non-stdlib dependencies.
- Do not compute `GLASSGATE_LIFT` from live smoke outputs.
- Do not change the default `run-live-dsh` 24-cell planned artifact.
- Do not reopen the J-lens rail.

## Step-by-Step Plan

1. Write failing tests for `run-live-smoke`, one-cell fake-transport execution,
   report propagation, and run-all propagation.
2. Extend `run_live_dsh` with optional bounded cell selection and run ID prefix.
3. Add CLI `run-live-smoke` that calls the bounded path.
4. Include live smoke in `build-report` and `run-all`.
5. Update docs and regenerate no-credential artifacts.
6. Run full verification and commit/push.

## Acceptance Criteria

- `run-live-smoke` writes `artifacts/live_smoke_seed_42/` by default.
- Default smoke artifact is blocked with zero adapter calls.
- Fake transport smoke executes exactly one adapter call, one cell, and one
  hidden verifier outcome.
- Smoke metrics include `cell_limit = 1`, `planned_task_runs = 1`, and no
  `GLASSGATE_LIFT`.
- Missing `--execute-live`, missing spend authorization, or missing prereg keeps
  smoke blocked even when a key is present.
- `build-report` and `run-all` expose live smoke status without treating it as
  macro evidence.
- Existing synthetic, macro, RQGM, J-lens, report, and run-all tests pass.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m py_compile claswarmed/*.py`
- `python3 -m broadcast_alpha run-live-gate --seed 42 --artifact-root artifacts`
- `python3 -m broadcast_alpha run-live-smoke --seed 42 --artifact-root artifacts --prereg prereg/PREREG_LIVE-01.md`
- `python3 -m broadcast_alpha run-live-dsh --seed 42 --tasks-per-cell 1 --artifact-root artifacts --prereg prereg/PREREG_LIVE-01.md`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts`
- `python3 -m broadcast_alpha export-ledger artifacts/live_smoke_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/live_smoke_seed_42 --agent agent_1 --step 3`
- `python3 -m broadcast_alpha export-ledger artifacts/live_dsh_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/live_dsh_seed_42 --agent agent_1 --step 3`
- `python3 -m broadcast_alpha export-ledger artifacts/final_report_seed_42 --format jsonl`
- `python3 -m broadcast_alpha export-ledger artifacts/run_all_seed_42 --format jsonl`
- `git diff --check`
- `git status --short --branch`

## Rollback Plan

Revert the live smoke commit and regenerate the prior live gate, live DSH,
final report, and run-all artifacts from the last pushed commit.

## Risks

| Risk | Mitigation |
|---|---|
| Secret leakage into artifacts | Tests scan artifacts for dummy key values; implementation stores presence booleans and sanitized response metadata only. |
| Accidental network or spend | Default path has `execute_live = false`; tests use injectable fake transport. |
| Overclaiming live behavior | Result cards and docs must distinguish blocked/fake smoke proof from real model-backed panel runs and state no live `GLASSGATE_LIFT` claim. |
| Accidental broad provider spend | Smoke command hard-limits to one cell and one task; full DSH remains a separate command. |
| Generated artifact churn obscures code review | Keep code/docs changes small and verify regenerated ledgers. |

## Proceed / Block Decision

Proceed. The pass does not require credentials, external spend, protected repo
mutation, or production deployment.
