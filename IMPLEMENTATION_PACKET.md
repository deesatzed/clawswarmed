# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Reopen the J-lens source gate without falsely claiming a runnable white-box
probe.

## Actual User Goal

Turn the old `JLENS-FREEZE-001` source blocker into an updated,
evidence-backed state: exact source verified, runtime/model/intervention still
frozen, with a novice-reproducible prompt packet and manual sanity template
ready for the next white-box step.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `tests/test_broadcast_alpha.py` | Add tests for exact source manifest, checked-in vignette packet, and manual sanity template. | Low |
| `broadcast_alpha/jlens.py` | Update source manifest and freeze reason from source-missing to source-verified/runtime-unavailable. | Low |
| `prereg/jlens_vignette_packet_01.json` | Add paired outcome-withheld/revealed prompts and label policy. | Low |
| `docs/JLENS_SOURCE_GATE.md`, `docs/JLENS_REOPEN_PACKET.md`, `docs/JLENS_MANUAL_SANITY_TEMPLATE.md` | Update the source gate and record the manual workflow. | Low |
| `FAILURE_LEDGER.md`, `prereg/PREREG_LEAK-01.md` | Preserve freeze history while recording source unblock. | Low |
| Workspace `DECISIONS.md`, `PROGRESS.md`, `GOAL_J_LENS.md` | Record current status and next gate. | Low |

## Existing Patterns To Follow

- Existing J-lens gate writes `metrics.json`, `sources.json`,
  `result_card.md`, `ledger.jsonl`, and replay contexts.
- Existing audit logic treats frozen J-lens as a valid defer, not completion.
- Failure history stays in `FAILURE_LEDGER.md`; amendments do not erase the
  original freeze.

## Assumptions

- The source commit SHA was verified with `git ls-remote` on 2026-07-08.
- Manual Neuronpedia checks may be useful but are not formal proof.
- No large model download or third-party source vendoring should happen in this
  slice.

## Non-Goals For This Pass

- No dependency install or model download.
- No real activation/Jacobian measurement.
- No causal or bridge claim.
- No vendor copy of `anthropics/jacobian-lens`.

## Step-by-Step Plan

1. Add failing tests for source manifest and new docs/artifacts.
2. Update `broadcast_alpha.jlens` manifest and result card.
3. Add the vignette packet and manual sanity template.
4. Update docs, failure ledger, prereg, and workspace truth docs.
5. Regenerate the checked-in J-lens gate artifact.
6. Run focused tests, full tests, compile checks, report/audit commands, and
   `git diff --check`.

## Acceptance Criteria

- `sources.json` records exact source URL, license, commit SHA, and access
  date.
- `metrics.json` records `required_exact_source_found = true` while
  `rail_status = frozen`.
- Vignette packet includes at least two paired prompts and single-token label
  shape checks.
- Manual sanity template states it is not formal proof.
- Full repo tests pass.

## Verification Plan

- `python3 -m unittest tests.test_broadcast_alpha.BroadcastAlphaTests.<jlens tests>`
- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m broadcast_alpha run-jlens-gate --seed 42`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
- `git diff --check`

## Rollback Plan

Revert the manifest updates, packet, docs, and generated J-lens artifact.
Existing macro/live rails are not altered in behavior.

## Risks

| Risk | Mitigation |
|---|---|
| Source verification gets overstated as J-lens proof. | Keep `rail_status = frozen` and label manual checks as non-proof. |
| Token labels are only whitespace-checked. | Mark the packet provisional until a selected tokenizer verifies labels. |
| Runtime work expands into model downloads. | Keep this slice source/docs/artifact only. |

## Proceed / Block Decision

Proceed. This is a bounded source-gate update that reduces uncertainty without
changing the formal proof threshold.
