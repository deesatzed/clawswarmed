# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Propagate the existing `run-live-sequence` rail into the consolidated
`build-report` surface and the unattended `run-all` bundle while preserving
no-spend defaults.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to a real unattended showpiece by making the
safe live-provider path visible in the same top-level artifacts as the macro
number, seed audit, RQGM trajectory, and J-lens defer record. A user should not
have to inspect a separate standalone artifact to see whether the live-provider
sequence is ready, blocked, or promoted.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `broadcast_alpha/reporting.py` | Add `live_sequence_seed_42` loading, result-table row, claim, metrics, and result-card text. | Report could overclaim a blocked sequence as live evidence. |
| `broadcast_alpha/orchestrator.py` | Run `run_live_sequence` in `run-all`, include it in child artifacts, run sequence, metrics, and replay text. | Could duplicate live gate/smoke artifacts or accidentally execute provider calls. |
| `tests/test_broadcast_alpha.py` | Add TDD assertions for report/run-all propagation. | Tests could only check presence, not the no-spend semantics. |
| `docs/FINAL_REPORT.md`, `docs/RUN_ALL.md`, `README.md` | Document live-sequence propagation and current blocked status. | Docs could imply the current evidence includes a live model call. |
| `artifacts/` | Regenerate final report and run-all artifacts in blocked no-credential mode. | Generated ledger churn. |
| Root `DECISIONS.md`, `PROGRESS.md` | Record workflow/progress update. | Root is not Git-backed. |

## Existing Patterns To Follow

- Rail functions return dataclasses with `run_id`, `artifact_path`, and
  `expected_replay`.
- Every rail writes `metrics.json`, `result_card.md`, `ledger.jsonl`, and
  `replay/contexts.json`.
- `run-live-gate`, `run-live-smoke`, `run-live-dsh`, and
  `run-live-sequence` already preserve no-secret artifacts and require
  explicit execution flags before provider calls.
- `run-all` uses nested source artifacts and child-ledger verification.
- Tests use fake/local transports for network-protected behavior.

## Assumptions

- No real OpenRouter request is allowed in this pass.
- `run-all` should call `run_live_sequence` with the same no-spend defaults as
  the separate live rails.
- The separate live gate, smoke, and DSH pilot rows should remain for continuity
  while the sequence becomes the preferred user path.

## Non-Goals For This Pass

- Do not run a live model-backed call.
- Do not call OpenRouter or any external API.
- Do not add non-stdlib dependencies.
- Do not compute `GLASSGATE_LIFT` from live sequence, smoke, or pilot outputs.
- Do not remove the existing live gate/smoke/DSH report fields.
- Do not reopen the J-lens rail.

## Step-by-Step Plan

1. Write failing tests that require `build-report` metrics/result table and
   `run-all` manifest/metrics to include live-sequence status.
2. Extend `build_result_report` with optional `live_sequence_seed_42`
   summarization and a no-run fallback.
3. Extend `run_all` to generate `live_sequence_seed_42` with no-spend defaults
   and propagate final-report fields.
4. Update docs and regenerate no-credential final report/run-all artifacts.
5. Run full verification and commit/push.

## Acceptance Criteria

- `build-report` metrics include live sequence status, adapter call total,
  smoke status, pilot status, promotion flag, and child-ledger verification.
- `result_table.json` includes a `live_sequence` row.
- `claim_matrix.json` includes a claim that the preferred live-provider
  sequence is blocked or recorded.
- `run-all` generates `source_artifacts/live_sequence_seed_42/`.
- `run-all` manifest, metrics, result card, and replay text include live
  sequence status.
- Default regenerated artifacts still record zero adapter calls and no live
  model run.
- Existing tests pass.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m py_compile claswarmed/*.py`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts`
- `python3 -m broadcast_alpha export-ledger artifacts/final_report_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/final_report_seed_42 --agent agent_1 --step 3`
- `python3 -m broadcast_alpha export-ledger artifacts/run_all_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/run_all_seed_42 --agent agent_1 --step 3`
- `python3 -m broadcast_alpha export-ledger artifacts/live_sequence_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/live_sequence_seed_42 --agent agent_1 --step 3`
- `git diff --check`
- secret scan for provider key patterns in code/docs/artifacts
- `git status --short --branch`

## Rollback Plan

Revert the propagation commit and regenerate the previous final report/run-all
artifacts from the last pushed commit.

## Risks

| Risk | Mitigation |
|---|---|
| Accidental network or spend | `run_all` calls the sequence with default no-execution flags and env stripped in regenerated artifacts. |
| Secret leakage into artifacts | Reuse existing env/status sanitizers and scan artifacts before commit. |
| Overclaiming live behavior | Metrics, claims, and docs state blocked/fake sequence outputs are not live macro evidence and do not produce `GLASSGATE_LIFT`. |
| Duplicate live rail records confuse users | Label the sequence as the preferred path and retain separate rails as underlying compatibility evidence. |

## Proceed / Block Decision

Proceed. The pass does not require credentials, external spend, protected repo
mutation, or production deployment.
