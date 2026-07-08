# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add the first executable J-lens outcome-leak readout probe without falsely
claiming the causal rail is proved.

## Actual User Goal

Move beyond the Hugging Face smoke by adding `run-jlens-leak-probe`, using the
checked-in paired vignettes, tokenizer-verified A/B labels, negative controls,
and sham readout controls to record a preregistered PC metric.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `tests/test_broadcast_alpha.py` | Add tests for leak-probe artifact creation, blocked missing runtime, and report/run-all integration. | Low |
| `broadcast_alpha/jlens_leak_probe.py` | New external outcome-leak readout runner and artifact writer. | Medium |
| `broadcast_alpha/cli.py` | Add `run-jlens-leak-probe`. | Low |
| `broadcast_alpha/reporting.py`, `broadcast_alpha/orchestrator.py`, `broadcast_alpha/goal_audit.py` | Surface leak-probe status without marking J-lens proved. | Medium |
| `prereg/PREREG_LEAK-01.md`, `FAILURE_LEDGER.md`, `docs/JLENS_SOURCE_GATE.md`, `docs/JLENS_REOPEN_PACKET.md` | Document the metric, null result, and current blocker. | Low |
| Workspace `DECISIONS.md`, `PROGRESS.md`, `GOAL_J_LENS.md` | Record current status and next gate. | Low |

## Existing Patterns To Follow

- Existing J-lens gate writes `metrics.json`, `sources.json`,
  `result_card.md`, `ledger.jsonl`, and replay contexts.
- Existing readiness/live commands are no-spend/no-network until explicitly
  authorized; this command follows the same artifact pattern.
- The external leak probe executes local PyTorch/Hugging Face code and requires
  the tiny model to already be available in the local Hugging Face cache.
- Existing audit logic treats frozen J-lens as a valid defer, not completion.
- Failure history stays in `FAILURE_LEDGER.md`; amendments do not erase the
  original freeze.

## Assumptions

- `hf-internal-testing/tiny-random-gpt2` is acceptable only as a smoke model,
  not as a meaningful gatekeeper.
- The model card does not declare a license in the observed Hugging Face
  metadata, so artifacts record `unknown_not_declared`.
- A passing tiny-HF leak-probe execution proves the readout path ran, but not
  that the outcome-leak hypothesis is true.
- No large model download or third-party source vendoring should happen here.

## Non-Goals For This Pass

- No large model download beyond the tiny cached smoke model.
- No causal intervention.
- No causal or bridge claim.
- No vendor copy of `anthropics/jacobian-lens`.

## Step-by-Step Plan

1. Add failing tests for leak-probe artifact creation and missing-runtime behavior.
2. Implement stdlib-only smoke wrapper that calls the external runtime.
3. Integrate leak-probe status into report, run-all, and goal audit.
4. Update docs and workspace truth files.
5. Regenerate the checked-in smoke, report, run-all, and audit artifacts.
6. Run focused tests, full tests, compile checks, report/audit commands, and
   `git diff --check`.

## Acceptance Criteria

- `run-jlens-leak-probe` writes `metrics.json`, `model_manifest.json`,
  `tokenizer_label_check.json`, `prereg_manifest.json`, `readouts.json`,
  `probe_payload.json`, result card, ledger, and replay context.
- The probe artifact records runtime versions, model source, model license,
  fitted source layers, PC metric, controls, and proof limitations.
- Report/run-all expose leak-probe status without changing the honest deferred
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
- `python3 -m broadcast_alpha run-jlens-gate --seed 42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
- `git diff --check`

## Rollback Plan

Revert `broadcast_alpha/jlens_leak_probe.py`, CLI/report/orchestrator/audit
integration, tests, docs, and generated leak-probe artifacts. Existing
macro/live rails and prior smoke artifacts are not altered in behavior.

## Risks

| Risk | Mitigation |
|---|---|
| Tiny-HF leak readout gets overstated as proof. | Keep `not_causal=true`, `causal_intervention_performed=false`, and `not_sufficient_for_JLENS_PROVED=true`. |
| Runtime path is missing on another machine. | Command writes a blocked artifact instead of failing silently. |
| Runtime work expands into large model downloads. | Keep this slice on the tiny cached HF model only. |

## Proceed / Block Decision

Proceed. This is a bounded readout update that tests the first PC metric
without changing the formal causal proof threshold.
