# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add the first local white-box J-lens runtime-readiness gate without falsely
claiming a runnable probe.

## Actual User Goal

Move beyond source verification by adding a `prepare-jlens-probe` command that
records whether the selected model source is white-box eligible, whether local
runtime dependencies exist, and whether verdict labels have been checked with a
selected tokenizer.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `tests/test_broadcast_alpha.py` | Add tests for black-box rejection, missing dependency recording, CLI artifact creation, and report/run-all integration. | Low |
| `broadcast_alpha/jlens_runtime.py` | New stdlib-only runtime-readiness artifact writer. | Low |
| `broadcast_alpha/cli.py` | Add `prepare-jlens-probe`. | Low |
| `broadcast_alpha/reporting.py`, `broadcast_alpha/orchestrator.py`, `broadcast_alpha/goal_audit.py` | Surface runtime readiness in report, run-all, and audit evidence. | Medium |
| `docs/JLENS_SOURCE_GATE.md`, `docs/JLENS_REOPEN_PACKET.md` | Document the runtime-readiness command and current blocker. | Low |
| Workspace `DECISIONS.md`, `PROGRESS.md`, `GOAL_J_LENS.md` | Record current status and next gate. | Low |

## Existing Patterns To Follow

- Existing J-lens gate writes `metrics.json`, `sources.json`,
  `result_card.md`, `ledger.jsonl`, and replay contexts.
- Existing readiness/live commands are no-spend/no-network until explicitly
  authorized; this command follows the same artifact pattern.
- Existing audit logic treats frozen J-lens as a valid defer, not completion.
- Failure history stays in `FAILURE_LEDGER.md`; amendments do not erase the
  original freeze.

## Assumptions

- `hf-internal-testing/tiny-random-gpt2` is a placeholder candidate for the
  first tiny Hugging Face smoke, not a proven final gatekeeper.
- Dependency readiness is checked by import availability only in this slice.
- No large model download or third-party source vendoring should happen here.

## Non-Goals For This Pass

- No dependency install or model download.
- No real activation/Jacobian measurement.
- No causal or bridge claim.
- No vendor copy of `anthropics/jacobian-lens`.

## Step-by-Step Plan

1. Add failing tests for runtime readiness and CLI artifact creation.
2. Implement stdlib-only readiness module and CLI command.
3. Integrate readiness status into report, run-all, and audit.
4. Update docs and workspace truth files.
5. Regenerate the checked-in runtime, report, run-all, and audit artifacts.
6. Run focused tests, full tests, compile checks, report/audit commands, and
   `git diff --check`.

## Acceptance Criteria

- `prepare-jlens-probe` rejects black-box provider sources for real J-lens.
- The readiness artifact records dependency availability, selected model ID,
  tokenizer-label status, and whether a real probe is runnable.
- Report/run-all/audit expose runtime readiness without changing the honest
  deferred verdict.
- Full repo tests pass.

## Verification Plan

- `python3 -m unittest tests.test_broadcast_alpha.BroadcastAlphaTests.<jlens tests>`
- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m broadcast_alpha prepare-jlens-probe --seed 42 --model-id hf-internal-testing/tiny-random-gpt2 --model-source huggingface`
- `python3 -m broadcast_alpha run-jlens-gate --seed 42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
- `git diff --check`

## Rollback Plan

Revert `broadcast_alpha/jlens_runtime.py`, CLI/report/orchestrator/audit
integration, tests, docs, and generated readiness artifacts. Existing macro/live
rails are not altered in behavior.

## Risks

| Risk | Mitigation |
|---|---|
| Runtime readiness gets overstated as J-lens proof. | Keep `not_activation_measurement`, `not_causal`, and `not_sufficient_for_JLENS_PROVED` true. |
| Token labels are only whitespace-checked. | Keep readiness blocked until a selected tokenizer verifies labels. |
| Runtime work expands into model downloads. | Keep this slice source/docs/artifact only. |

## Proceed / Block Decision

Proceed. This is a bounded runtime-readiness update that makes the next blocker
explicit without changing the formal proof threshold.
