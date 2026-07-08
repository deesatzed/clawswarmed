# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add the first Hugging Face/open-weight J-lens fit/apply smoke without falsely
claiming the outcome-leak or causal rail is proved.

## Actual User Goal

Move beyond the reference tiny-decoder smoke by adding a
`run-jlens-hf-smoke` command that loads a tiny Hugging Face decoder from the
external J-lens runtime, verifies tokenizer labels, and records a real
`jlens.fit()` plus `JacobianLens.apply()` pass.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `tests/test_broadcast_alpha.py` | Add tests for HF smoke artifact creation, blocked missing runtime, and report/run-all integration. | Low |
| `broadcast_alpha/jlens_hf_smoke.py` | New external Hugging Face smoke runner and artifact writer. | Medium |
| `broadcast_alpha/cli.py` | Add `run-jlens-hf-smoke`. | Low |
| `broadcast_alpha/reporting.py`, `broadcast_alpha/orchestrator.py` | Surface smoke status in report and run-all evidence. | Medium |
| `docs/JLENS_SOURCE_GATE.md`, `docs/JLENS_REOPEN_PACKET.md` | Document the runtime-readiness command and current blocker. | Low |
| Workspace `DECISIONS.md`, `PROGRESS.md`, `GOAL_J_LENS.md` | Record current status and next gate. | Low |

## Existing Patterns To Follow

- Existing J-lens gate writes `metrics.json`, `sources.json`,
  `result_card.md`, `ledger.jsonl`, and replay contexts.
- Existing readiness/live commands are no-spend/no-network until explicitly
  authorized; this command follows the same artifact pattern.
- The external smoke executes local PyTorch/Hugging Face code and requires the
  tiny model to already be available in the local Hugging Face cache.
- Existing audit logic treats frozen J-lens as a valid defer, not completion.
- Failure history stays in `FAILURE_LEDGER.md`; amendments do not erase the
  original freeze.

## Assumptions

- `hf-internal-testing/tiny-random-gpt2` is acceptable only as a smoke model,
  not as a meaningful gatekeeper.
- The model card does not declare a license in the observed Hugging Face
  metadata, so artifacts record `unknown_not_declared`.
- A passing HF tiny smoke proves the adapter/runtime path can fit/apply locally,
  but not that the outcome-leak hypothesis is true.
- No large model download or third-party source vendoring should happen here.

## Non-Goals For This Pass

- No large model download beyond the tiny cached smoke model.
- No outcome-leak probe.
- No causal intervention.
- No causal or bridge claim.
- No vendor copy of `anthropics/jacobian-lens`.

## Step-by-Step Plan

1. Add failing tests for HF smoke artifact creation and missing-runtime behavior.
2. Implement stdlib-only smoke wrapper that calls the external runtime.
3. Integrate HF smoke status into report and run-all.
4. Update docs and workspace truth files.
5. Regenerate the checked-in smoke, report, run-all, and audit artifacts.
6. Run focused tests, full tests, compile checks, report/audit commands, and
   `git diff --check`.

## Acceptance Criteria

- `run-jlens-hf-smoke` writes `metrics.json`, `model_manifest.json`,
  `tokenizer_label_check.json`, `smoke_payload.json`, result card, ledger, and
  replay context.
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
- `python3 -m broadcast_alpha run-jlens-hf-smoke --seed 42 --model-id hf-internal-testing/tiny-random-gpt2`
- `python3 -m broadcast_alpha run-jlens-gate --seed 42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
- `git diff --check`

## Rollback Plan

Revert `broadcast_alpha/jlens_hf_smoke.py`, CLI/report/orchestrator
integration, tests, docs, and generated HF smoke artifacts. Existing macro/live
rails and the prior reference smoke are not altered in behavior.

## Risks

| Risk | Mitigation |
|---|---|
| HF tiny smoke gets overstated as outcome-leak proof. | Keep `outcome_leak_probe_performed=false`, `not_causal=true`, and `not_sufficient_for_JLENS_PROVED=true`. |
| Runtime path is missing on another machine. | Command writes a blocked artifact instead of failing silently. |
| Runtime work expands into large model downloads. | Keep this slice on the tiny cached HF model only. |

## Proceed / Block Decision

Proceed. This is a bounded smoke update that proves the Hugging Face model path
runs locally without changing the formal proof threshold.
