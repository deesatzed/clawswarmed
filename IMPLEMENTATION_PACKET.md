# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add committed preregistration provenance to the gated `run-live-dsh` pilot.
The pilot should name `PREREG_LIVE-01.md` in metrics, receipts, result cards,
the final report, and the unattended bundle before any provider-backed run is
eligible to count as evidence.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to a real replayable Glass Gate instrument by
making the live DSH rail preregistered and auditable. The harness must still
not claim a real live result until provider credentials, model, spend
authorization, and live execution are explicitly supplied.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `prereg/PREREG_LIVE-01.md` | Add the committed live DSH pilot preregistration. | Could be too vague to constrain later live runs. |
| `broadcast_alpha/live_dsh.py` | Accept prereg path, record prereg ID/path/existence in receipts, metrics, and result card. | Could incorrectly treat a missing prereg as acceptable live evidence. |
| `broadcast_alpha/cli.py` | Add `run-live-dsh --prereg` defaulting to `prereg/PREREG_LIVE-01.md`. | CLI default could drift from run-all/report defaults. |
| `broadcast_alpha/reporting.py` | Surface live DSH prereg metadata in consolidated metrics and claims. | Report could overstate blocked/fake pilot evidence. |
| `broadcast_alpha/orchestrator.py` | Pass the live prereg into `run-live-dsh` and expose bundle metadata. | Run-all could omit the live prereg from nested artifacts. |
| `tests/test_broadcast_alpha.py` | Add TDD coverage for prereg file, live DSH metrics/ledger/card, CLI default, report, and run-all. | Tests may overfit path strings. |
| `docs/LIVE_DSH_PILOT.md` | Document preregistration and live-execution gates. | Docs could overclaim live behavior. |
| `README.md`, `docs/RUN_ALL.md`, `docs/FINAL_REPORT.md` | Update current artifact descriptions with live DSH prereg metadata. | Drift between docs and artifacts. |
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
- Macro DSH and RQGM commands already accept explicit prereg paths and store
  prereg IDs in their metrics.
- The deterministic DSH rail already defines panel types, workspace arms, seed
  conditions, task bank records, metrics files, replay bundles, and ledgers.
- The live DSH rail already records blocked/default artifacts, fake-transport
  pilot outputs, structured patch parsing, and hidden verifier outcomes.

## Assumptions

- No real OpenRouter request is allowed in this pass.
- A committed `PREREG_LIVE-01.md` should exist before any real live DSH pilot is
  eligible to count as evidence.
- A fake transport can prove task-cell orchestration, structured patch parsing,
  hidden-test verification, replay, ledgering, prereg metadata, and no-secrets
  artifact behavior.
- Future real execution must require all four conditions: key present, model
  selected, `--authorize-api-spend`, and `--execute-live`.

## Non-Goals For This Pass

- Do not run a live model-backed panel.
- Do not call OpenRouter or any external API.
- Do not add non-stdlib dependencies.
- Do not implement the full live DSH macro grid.
- Do not compute `GLASSGATE_LIFT` from blocked or fake-transport live DSH
  outputs.
- Do not reopen the J-lens rail.

## Step-by-Step Plan

1. Write failing tests for `PREREG_LIVE-01.md`, live DSH prereg metrics,
   ledger/result-card metadata, CLI defaults, report propagation, and run-all
   propagation.
2. Add `prereg/PREREG_LIVE-01.md` with no-default-spend, no-secret, no-live-
   claim, verifier, and kill/defer criteria.
3. Add `prereg_path` support to `run_live_dsh`.
4. Add CLI `--prereg` and pass the live prereg from `run-all`.
5. Propagate live prereg metadata into `build-report` and `run-all` metrics.
6. Update docs and regenerate no-credential artifacts.
7. Run full verification and commit/push.

## Acceptance Criteria

- `prereg/PREREG_LIVE-01.md` exists and explicitly forbids default spend and
  `GLASSGATE_LIFT` claims from blocked/fake runs.
- Live DSH metrics include `prereg_id`, `prereg_path`, and `prereg_exists`.
- The live DSH run-start ledger receipt and result card include the prereg ID.
- CLI default `run-live-dsh` uses `prereg/PREREG_LIVE-01.md`.
- Final report and run-all metrics expose the live DSH prereg ID.
- Missing `--execute-live` or missing spend authorization keeps the pilot
  blocked even when a key is present.
- Default `run-all` still records no live model run or pilot execution.
- Existing synthetic, macro, RQGM, J-lens, report, and run-all tests pass.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m broadcast_alpha run-live-gate --seed 42 --artifact-root artifacts`
- `python3 -m broadcast_alpha run-live-dsh --seed 42 --tasks-per-cell 1 --artifact-root artifacts --prereg prereg/PREREG_LIVE-01.md`
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
| Overclaiming live behavior | Result cards and docs must distinguish blocked/fake pilot proof from real model-backed panel runs and state no live `GLASSGATE_LIFT` claim. |
| Missing prereg file in future execution | Metrics record `prereg_exists`; docs require committed prereg before provider execution is interpreted. |
| Generated artifact churn obscures code review | Keep code/docs changes small and verify regenerated ledgers. |

## Proceed / Block Decision

Proceed. The pass does not require credentials, external spend, protected repo
mutation, or production deployment.
