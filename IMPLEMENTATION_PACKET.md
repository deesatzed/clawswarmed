# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add verifier-backed candidate outcomes to the gated `run-live-dsh` pilot.
Adapter output should be able to carry a structured patch, which the pilot
parses and runs through the existing hidden-test verifier.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to a real replayable Glass Gate instrument by
turning live-panel adapter responses into verifier-backed task outcomes. The
harness must still not claim a real live result until provider credentials,
model, spend authorization, and live execution are explicitly supplied.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `broadcast_alpha/live_dsh.py` | Parse structured adapter patches, run hidden verifier, and record outcome metrics. | Could overclaim fake transport verifier outcomes as live evidence. |
| `tests/test_broadcast_alpha.py` | Add TDD coverage for fake-transport patch verification and parse failure behavior. | Tests may overfit response formatting. |
| `docs/LIVE_DSH_PILOT.md` | Document structured patch format and verifier-backed outcome boundary. | Docs could overclaim live behavior. |
| `docs/LIVE_MODEL_GATE.md` | Keep adapter and pilot boundary current. | Docs could overclaim live behavior. |
| `README.md`, `docs/RUN_ALL.md`, `docs/FINAL_REPORT.md` | Update current artifact descriptions if metrics change. | Drift between docs and artifacts. |
| `artifacts/` | Regenerate live gate, final report, and run-all artifacts without real credentials. | Ledger churn in generated bundles. |
| Root `DECISIONS.md`, `PROGRESS.md` | Record security/workflow decision and progress. | Root is not Git-backed. |

## Existing Patterns To Follow

- Rail functions return dataclasses with `run_id`, `artifact_path`, and
  `expected_replay`.
- Every rail writes `metrics.json`, `result_card.md`, `ledger.jsonl`, and
  `replay/contexts.json`.
- `run-all` nests child artifacts and copies their ledger status into the
  final report.
- Tests use fake/local transports for any behavior that would otherwise require
  network or credentials.
- The deterministic DSH rail already defines panel types, workspace arms, seed
  conditions, task bank records, metrics files, replay bundles, and ledgers.
- The task bank already exposes `verify_patch()` for hidden-test verification.

## Assumptions

- No real OpenRouter request is allowed in this pass.
- A fake transport can prove task-cell orchestration, structured patch parsing,
  hidden-test verification, replay, ledgering, and no-secrets artifact behavior.
- Future real execution must require all four conditions: key present, model
  selected, `--authorize-api-spend`, and `--execute-live`.

## Non-Goals For This Pass

- Do not run a live model-backed panel.
- Do not call OpenRouter or any external API.
- Do not add non-stdlib dependencies.
- Do not implement the full live DSH macro grid.
- Do not compute `GLASSGATE_LIFT` from fake-transport outputs.
- Do not reopen the J-lens rail.

## Step-by-Step Plan

1. Write failing tests for fake-transport JSON patch output and parse failures.
2. Implement patch extraction from adapter message content.
3. Run `verify_patch()` for parsed patches and record per-task outcomes.
4. Add pilot outcome metrics and ledger receipts.
5. Update docs and regenerate no-credential artifacts.
6. Run full verification and commit/push.

## Acceptance Criteria

- Fake transport execution can return JSON `{"patch": "..."}` content.
- Parsed patches are run through the hidden verifier and recorded per task.
- Metrics include candidate patch count, verifier pass count, and verifier pass
  rate.
- Missing `--execute-live` or missing spend authorization keeps the pilot
  blocked even when a key is present.
- Default `run-all` still records no live model run or pilot execution.
- Existing synthetic, macro, RQGM, J-lens, report, and run-all tests pass.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m broadcast_alpha run-live-gate --seed 42 --artifact-root artifacts`
- `python3 -m broadcast_alpha run-live-dsh --seed 42 --artifact-root artifacts`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts`
- `python3 -m broadcast_alpha export-ledger artifacts/live_dsh_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/live_dsh_seed_42 --agent agent_1 --step 3`
- `python3 -m broadcast_alpha export-ledger artifacts/live_gate_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/live_gate_seed_42 --agent agent_1 --step 3`
- `git diff --check`
- `git status --short --branch`

## Rollback Plan

Revert the live DSH pilot commit and regenerate the prior live gate, final
report, and run-all artifacts from the last pushed commit.

## Risks

| Risk | Mitigation |
|---|---|
| Secret leakage into artifacts | Tests scan artifacts for dummy key values; implementation stores presence booleans and sanitized response metadata only. |
| Accidental network or spend | Default path has `execute_live = false`; tests use injectable fake transport. |
| Overclaiming live behavior | Result cards and docs must distinguish fake-transport pilot proof from real model-backed panel runs. |
| Generated artifact churn obscures code review | Keep code/docs changes small and verify regenerated ledgers. |

## Proceed / Block Decision

Proceed. The pass does not require credentials, external spend, protected repo
mutation, or production deployment.
