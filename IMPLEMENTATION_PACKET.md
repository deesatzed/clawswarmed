# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add the first executable J-lens causal-intervention gate without falsely
claiming the causal rail is proved.

## Actual User Goal

Move beyond the null leak probe by adding `run-jlens-intervention`, a
replayable gate that blocks causal intervention when the preregistered PC signal
is below threshold.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `tests/test_broadcast_alpha.py` | Add tests for intervention-gate artifact creation, missing leak probe, and report/run-all integration. | Low |
| `broadcast_alpha/jlens_intervention.py` | New causal-intervention gate and artifact writer. | Medium |
| `broadcast_alpha/cli.py` | Add `run-jlens-intervention`. | Low |
| `broadcast_alpha/reporting.py`, `broadcast_alpha/orchestrator.py`, `broadcast_alpha/goal_audit.py` | Surface intervention-gate status without marking J-lens proved. | Medium |
| `prereg/PREREG_CAUSAL-01.md`, `FAILURE_LEDGER.md`, `docs/JLENS_SOURCE_GATE.md`, `docs/JLENS_REOPEN_PACKET.md` | Document the blocked intervention and current blocker. | Low |
| Workspace `DECISIONS.md`, `PROGRESS.md`, `GOAL_J_LENS.md` | Record current status and next gate. | Low |

## Existing Patterns To Follow

- Existing J-lens gate writes `metrics.json`, `sources.json`,
  `result_card.md`, `ledger.jsonl`, and replay contexts.
- Existing readiness/live commands are no-spend/no-network until explicitly
  authorized; this command follows the same artifact pattern.
- The intervention gate consumes the checked-in leak-probe metrics and does not
  run external model code unless a future implementation adds real intervention.
- Existing audit logic treats frozen J-lens as a valid defer, not completion.
- Failure history stays in `FAILURE_LEDGER.md`; amendments do not erase the
  original freeze.

## Assumptions

- `hf-internal-testing/tiny-random-gpt2` is acceptable only as a smoke model,
  not as a meaningful gatekeeper.
- The model card does not declare a license in the observed Hugging Face
  metadata, so artifacts record `unknown_not_declared`.
- A blocked intervention gate proves the preregistered no-signal stop rule ran,
  but not that the causal hypothesis is true.
- No large model download or third-party source vendoring should happen here.

## Non-Goals For This Pass

- No large model download beyond the tiny cached smoke model.
- No causal intervention.
- No causal or bridge claim.
- No vendor copy of `anthropics/jacobian-lens`.

## Step-by-Step Plan

1. Add failing tests for intervention-gate artifact creation and missing leak-probe behavior.
2. Implement stdlib-only intervention gate that reads leak-probe metrics.
3. Integrate intervention status into report, run-all, and goal audit.
4. Update docs and workspace truth files.
5. Regenerate the checked-in smoke, report, run-all, and audit artifacts.
6. Run focused tests, full tests, compile checks, report/audit commands, and
   `git diff --check`.

## Acceptance Criteria

- `run-jlens-intervention` writes `metrics.json`, `prereg_manifest.json`,
  `decision.json`, result card, ledger, and replay context.
- The intervention artifact records source leak-probe PC, threshold, decision,
  reason codes, and proof limitations.
- Report/run-all expose intervention status without changing the honest deferred
  verdict.
- Full repo tests pass.

## Verification Plan

- `python3 -m unittest tests.test_broadcast_alpha.BroadcastAlphaTests.<jlens tests>`
- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m broadcast_alpha prepare-jlens-probe --seed 42 --model-id hf-internal-testing/tiny-random-gpt2 --model-source huggingface`
- `python3 -m broadcast_alpha run-jlens-smoke --seed 42`
- `python3 -m broadcast_alpha run-jlens-hf-smoke --seed 42 --model-id hf-internal-testing/tiny-random-gpt2`
- `python3 -m broadcast_alpha run-jlens-leak-probe --seed 42 --model-id hf-internal-testing/tiny-random-gpt2`
- `python3 -m broadcast_alpha run-jlens-intervention --seed 42`
- `python3 -m broadcast_alpha run-jlens-gate --seed 42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
- `git diff --check`

## Rollback Plan

Revert `broadcast_alpha/jlens_intervention.py`, CLI/report/orchestrator/audit
integration, tests, docs, and generated intervention artifacts. Existing
macro/live rails and prior J-lens artifacts are not altered in behavior.

## Risks

| Risk | Mitigation |
|---|---|
| Blocked intervention gets overstated as proof. | Keep `causal_intervention_performed=false`, `sham_intervention_control_performed=false`, and `not_sufficient_for_JLENS_PROVED=true`. |
| Leak-probe artifact is missing. | Command writes `blocked_missing_leak_probe` instead of failing silently. |
| Null signal is routed around. | Gate uses the preregistered PC threshold and records `blocked_no_differential_signal`. |

## Proceed / Block Decision

Proceed. This is a bounded intervention-gate update that strengthens the clean
defer record without changing the formal causal proof threshold.
