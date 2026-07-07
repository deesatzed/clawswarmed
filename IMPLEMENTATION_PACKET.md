# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add a `audit-goal` evidence rail that reads current repo files and generated
artifacts, emits a requirement-by-requirement Glass Gate status matrix, and
records remaining gaps without claiming completion.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to a finishable research instrument by making
the completion gate executable and auditable. The user should be able to run a
command that says which required claims are proved by current artifacts, which
rails are cleanly deferred, and which requirements remain incomplete.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `broadcast_alpha/goal_audit.py` | New audit rail with requirement matrix, metrics, replay, result card, and ledger. | Could overstate completion if statuses are too broad. |
| `broadcast_alpha/cli.py` | Add `audit-goal` command. | CLI could be confused with final completion. |
| `tests/test_broadcast_alpha.py` | Add TDD coverage for audit artifact, conservative statuses, CLI replay, and ledger verification. | Tests could bake in weak evidence. |
| `docs/GOAL_AUDIT.md`, `README.md` | Document the audit command and current conservative verdict. | Docs could become stale if the audit output changes. |
| `artifacts/goal_audit_seed_42/` | Generated current audit artifact. | Generated ledger churn. |
| Root `DECISIONS.md`, `PROGRESS.md` | Record workflow/progress update. | Root is not Git-backed. |

## Existing Patterns To Follow

- Rail functions return dataclasses with `run_id`, `artifact_path`, and
  `expected_replay`.
- Every rail writes `metrics.json`, `result_card.md`, `ledger.jsonl`, and
  `replay/contexts.json`.
- `build-report` and `run-all` already produce consolidated metrics with
  macro, seed audit, RQGM, J-lens, and live sequence fields.
- Ledgers are verified through `Ledger.from_jsonl(...).verify_chain()`.
- Tests use fake/local transports for network-protected behavior.

## Assumptions

- No real OpenRouter request is allowed in this pass.
- The audit should be conservative and mark the overall goal incomplete while a
  real live/model-backed run is absent.
- A frozen J-lens rail with `JLENS-FREEZE-001` is a clean defer record, not a
  pass for mechanistic claims.
- The command reads existing artifacts; it does not run experiments.

## Non-Goals For This Pass

- Do not run a live model-backed call.
- Do not call OpenRouter or any external API.
- Do not add non-stdlib dependencies.
- Do not change macro, RQGM, live, or report outputs except adding the audit.
- Do not mark `GOAL_GLASSGATE.md` complete.
- Do not reopen the J-lens rail.

## Step-by-Step Plan

1. Write failing tests for `audit_goal` and CLI `audit-goal`.
2. Implement `broadcast_alpha.goal_audit.audit_goal`.
3. Add CLI command.
4. Document the audit rail and generate `artifacts/goal_audit_seed_42/`.
5. Run verification and commit/push.

## Acceptance Criteria

- `audit-goal` writes `artifacts/goal_audit_seed_42/`.
- Audit artifact includes `requirements.json`, `metrics.json`,
  `result_card.md`, `ledger.jsonl`, and `replay/contexts.json`.
- Requirements include proved entries for macro `GLASSGATE_LIFT`, D arms,
  seed audit, run-all bundle, replay/ledger evidence, and RQGM epochs.
- Requirements include a deferred J-lens/bridge/mechanistic record when the
  J-lens freeze evidence exists.
- Requirements include an incomplete live/model-backed execution record while
  adapter calls remain zero.
- Overall audit status is not complete until incomplete requirements are gone.
- Existing tests pass.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m py_compile claswarmed/*.py`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42`
- `python3 -m broadcast_alpha summarize artifacts/goal_audit_seed_42`
- `python3 -m broadcast_alpha export-ledger artifacts/goal_audit_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/goal_audit_seed_42 --agent agent_1 --step 3`
- `git diff --check`
- secret scan for provider key patterns in code/docs/artifacts
- `git status --short --branch`

## Rollback Plan

Revert the audit rail commit and remove `artifacts/goal_audit_seed_42/`.

## Risks

| Risk | Mitigation |
|---|---|
| Overclaiming completion | Use explicit `proved`, `deferred_with_record`, and `incomplete` statuses, and make any incomplete item force non-complete overall status. |
| Audit drift | Source audit fields directly from current artifacts and docs, not hand-written constants where evidence exists. |
| Generated artifact mistaken for final signoff | Result card states that the broader goal remains incomplete while live/model-backed execution is absent. |
| Secret leakage | Audit reads sanitized metrics only and the final verification includes a secret scan. |

## Proceed / Block Decision

Proceed. The pass does not require credentials, external spend, protected repo
mutation, or production deployment.
