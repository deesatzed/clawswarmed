# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add the first external J-lens fit/apply smoke without falsely claiming the
outcome-leak or causal rail is proved.

## Actual User Goal

Move beyond readiness by cloning/installing the Anthropic reference
implementation outside the app repo and adding a `run-jlens-smoke` command that
records a real `jlens.fit()` plus `JacobianLens.apply()` pass on the reference
CPU-only tiny decoder.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `tests/test_broadcast_alpha.py` | Add tests for smoke artifact creation, blocked missing runtime, and report/run-all integration. | Low |
| `broadcast_alpha/jlens_smoke.py` | New external smoke runner and artifact writer. | Medium |
| `broadcast_alpha/cli.py` | Add `run-jlens-smoke`. | Low |
| `broadcast_alpha/reporting.py`, `broadcast_alpha/orchestrator.py` | Surface smoke status in report and run-all evidence. | Medium |
| `docs/JLENS_SOURCE_GATE.md`, `docs/JLENS_REOPEN_PACKET.md` | Document the runtime-readiness command and current blocker. | Low |
| Workspace `DECISIONS.md`, `PROGRESS.md`, `GOAL_J_LENS.md` | Record current status and next gate. | Low |

## Existing Patterns To Follow

- Existing J-lens gate writes `metrics.json`, `sources.json`,
  `result_card.md`, `ledger.jsonl`, and replay contexts.
- Existing readiness/live commands are no-spend/no-network until explicitly
  authorized; this command follows the same artifact pattern.
- The external smoke may execute local PyTorch code but does not download model
  weights.
- Existing audit logic treats frozen J-lens as a valid defer, not completion.
- Failure history stays in `FAILURE_LEDGER.md`; amendments do not erase the
  original freeze.

## Assumptions

- The reference `TinyDecoder` is Apache-2.0 test code from the cloned
  `anthropics/jacobian-lens` repo.
- A passing tiny smoke proves the reference implementation can fit/apply in
  this runtime, but not that the outcome-leak hypothesis is true.
- No large model download or third-party source vendoring should happen here.

## Non-Goals For This Pass

- No large model download.
- No outcome-leak probe.
- No causal intervention.
- No causal or bridge claim.
- No vendor copy of `anthropics/jacobian-lens`.

## Step-by-Step Plan

1. Add failing tests for smoke artifact creation and missing-runtime behavior.
2. Implement stdlib-only smoke wrapper that calls the external runtime.
3. Integrate smoke status into report and run-all.
4. Update docs and workspace truth files.
5. Regenerate the checked-in smoke, report, run-all, and audit artifacts.
6. Run focused tests, full tests, compile checks, report/audit commands, and
   `git diff --check`.

## Acceptance Criteria

- `run-jlens-smoke` writes `metrics.json`, `smoke_payload.json`, result card,
  ledger, and replay context.
- The smoke artifact records repo commit, runtime versions, model source,
  model license, fitted source layers, and proof limitations.
- Report/run-all expose smoke status without changing the honest deferred
  verdict.
- Full repo tests pass.

## Verification Plan

- `python3 -m unittest tests.test_broadcast_alpha.BroadcastAlphaTests.<jlens tests>`
- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m broadcast_alpha prepare-jlens-probe --seed 42 --model-id hf-internal-testing/tiny-random-gpt2 --model-source huggingface`
- `python3 -m broadcast_alpha run-jlens-smoke --seed 42`
- `python3 -m broadcast_alpha run-jlens-gate --seed 42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
- `git diff --check`

## Rollback Plan

Revert `broadcast_alpha/jlens_smoke.py`, CLI/report/orchestrator integration,
tests, docs, and generated smoke artifacts. Existing macro/live rails are not
altered in behavior.

## Risks

| Risk | Mitigation |
|---|---|
| Tiny smoke gets overstated as outcome-leak proof. | Keep `outcome_leak_probe_performed=false`, `not_causal=true`, and `not_sufficient_for_JLENS_PROVED=true`. |
| Runtime path is missing on another machine. | Command writes a blocked artifact instead of failing silently. |
| Runtime work expands into model downloads. | Keep this slice on the reference tiny decoder only. |

## Proceed / Block Decision

Proceed. This is a bounded smoke update that proves the reference implementation
runs locally without changing the formal proof threshold.
