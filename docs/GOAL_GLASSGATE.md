# GOAL_GLASSGATE.md

Use this as the next Codex `/goal` when evaluating the Glass Gate pathway.

```text
/goal

OUTCOME:
Build `clawswarmed` into the Broadcast-alpha / Glass Gate research instrument
described by `/Volumes/WS4TB/claswarmed/HANDOFF_claswarmed_glassgate_v1_2.md`.

The finished v1 instrument must run a replayable, tamper-evident experiment
that answers one question:

When one agent has the correct minority insight and most agents have plausible
wrong or incomplete information, does the communication structure preserve the
right dissent without also admitting wrong dissent?

The main output is:

GLASSGATE_LIFT = D(scarce_protected) - max(D(abundant), D(random), D(scarce_naive_topk))

where:

D(arm) = influence(correct_minority_seed) - influence(incorrect_minority_seed)

The build is not complete if it is only a planner, dashboard, model router,
agent chat UI, or generic orchestration framework.

RAW IDEA:
Create an instrument, not a product. It should rig checkable tasks with correct
and incorrect minority seeds, vary communication structure, log everything,
replay any run, and emit one falsifiable number plus confidence intervals and
replay artifacts.

TASK TYPE:
Multi-phase implementation + research/audit harness + safety/provenance
instrumentation.

CURRENT STARTING POINT:
- Workspace container: `/Volumes/WS4TB/claswarmed`
- Git-backed app repo: `/Volumes/WS4TB/claswarmed/claswarmed-app`
- Remote: `https://github.com/deesatzed/clawswarmed.git`
- Safe checkpoint tag: `checkpoint/pre-new-pathway-2026-07-07`
- Checkpoint commit: `0bf6de8763c0823f77e7deb4dd8f6365118bf8a4`
- Current app package `claswarmed/` is a useful prior scaffold, not the final
  Glass Gate instrument.

FIRST REQUIRED STEP:
Before editing, verify the checkpoint:

cd /Volumes/WS4TB/claswarmed/claswarmed-app
git status --short --branch
git rev-parse checkpoint/pre-new-pathway-2026-07-07^{}
python3 -m unittest discover -s tests
python3 -m py_compile claswarmed/*.py

If the repo is dirty or the checkpoint tag is missing, stop and report.

PROOF OF DONE:
1. Repository and preregistration:
   - `README.md` says this is a research instrument, not a product.
   - `HANDOFF_claswarmed_glassgate_v1_2.md` is copied into the app repo under
     `docs/` or `docs/archive/` with provenance.
   - `FAILURE_LEDGER.md` exists with the 12 pre-seeded failure modes from the
     handoff.
   - `prereg/` contains at least:
     `PREREG_DSH-01.md`, `PREREG_PART-01.md`, `PREREG_LEAK-01.md`,
     `PREREG_CAUSAL-01.md`, `PREREG_EPOCH-01.md`,
     `PREREG_BRIDGE-01.md`, `PREREG_MECHADMIT-01.md`, and
     `PREREG_LIVE-01.md`.

2. Contracts and ledger:
   - Implement `broadcast_alpha/` as the primary instrument package.
   - Candidate, receipt, slot, evaluator, epoch, metrics, and task contracts
     exist as dataclasses and/or JSON Schemas.
   - Append-only ledger supports chained hashes and parent hashes.
   - `verify_chain()` passes after at least 10,000 mixed synthetic receipts.
   - Tampering with a receipt breaks ledger verification.
   - Tombstoning masks current authority but preserves historical replay.

3. Replay:
   - Replay reconstructs visible agent context byte-exact for a saved run.
   - `python3 -m broadcast_alpha replay artifacts/<run_id> --agent agent_1 --step 3`
     works on a generated artifact.

4. Synthetic-first harness:
   - No LLM/API tokens are used before this proof item passes.
   - Scripted deterministic agents can run a complete synthetic pipeline:
     ledger -> candidates -> gate -> board -> decision -> verifier -> metrics.
   - Workspace arms implemented:
     `abundant`, `random`, `scarce_naive_topk`, `scarce_protected`.
   - Seed conditions implemented:
     `correct_minority`, `incorrect_minority`, `none`.
   - Panel types implemented:
     `correlated_shared_context`, `partitioned_disjoint_shards`.
   - Fixed-seed random gate is reproducible.
   - Unit test confirms: influence 6/10 correct and 2/10 incorrect yields
     `D = 0.4`.
   - Unit test confirms `GLASSGATE_LIFT` formula exactly.
   - `result_card.md` and `metrics.json` are generated for a synthetic run.

5. First meaningful macro run:
   - After synthetic tests pass, run a preregistered macro grid:
     `2 panel types x 4 workspace arms x 3 seed conditions = 24 cells`.
   - Use at least 30 tasks/cell unless blocked by task-bank size; if blocked,
     record the blocker and run the largest balanced grid available.
   - Report:
     `GLASSGATE_LIFT`, 95% bootstrap CI, D by arm, D by panel type,
     verified solve rate, panel correlation rho, candidate ablation rate,
     token cost per solve if applicable, and replay bundle path.
   - Candidate-level ablation is run for an attribution sample.
   - The result may be positive, negative, or null. Any result is acceptable if
     it is preregistered, replayable, and honestly interpreted.

6. RQGM / epoch layer:
   - Implement controlled evaluator evolution, not uncontrolled
     self-improvement.
   - Within an epoch, evaluator/gate semantics are frozen.
   - At epoch boundaries, challenger gates are evaluated on held-out anchored
     tasks.
   - Replacement requires improvement on D and GLASSGATE_LIFT by the
     preregistered margin, seed camouflage near chance, no unacceptable solve
     degradation, and no active J-lens veto if the J-lens rail is alive.
   - Run at least 5 epochs in a synthetic or macro-safe configuration.
   - Tombstoned scores remain historically replayable but are absent from
     current ranking.

7. J-lens / Glass Gate rail:
   - First implement a `NullJLensProbe` interface and tests.
   - Before implementing a real J-lens probe, locate and cite the exact paper,
     repo, or implementation being used. Do not rely on an uncited memory of an
     "Anthropic paper".
   - A white-box gatekeeper means gradient/layer access. It may be local or
     cloud-hosted, but layer access is the point.
   - Single-token verdict checks must pass for all J-lens-critical labels.
   - If a real probe can run, export layer/position activation data.
   - If the weekend probe is flat or the source/model is unavailable, freeze the
     J-lens rail, record the failure in `FAILURE_LEDGER.md`, and continue the
     macro/RQGM rails.
   - Timing/readout alone is not causality. Any causal J-lens claim requires
     ablation, swap, suppression, or sham-control comparison.

8. Optional bridge/mechanistic rails:
   - Run Phase 4 bridge only if the J-lens rail remains alive.
   - Run Phase 5 mechanistic admission only if white-box candidate-generating
     agents and J-space features are available.
   - If unavailable, document as a clean kill/defer decision, not as a partial
     success.

9. Required tests:
   Implement and pass tests equivalent to:
   - `test_ledger_append_and_verify`
   - `test_ledger_tamper_detection`
   - `test_replay_byte_exact`
   - `test_discrimination_formula`
   - `test_glassgate_lift_formula`
   - `test_random_gate_reproducibility`
   - `test_naive_topk_orders_by_score`
   - `test_protected_gate_reserves_dissent_slots`
   - `test_seed_camouflage_auc_flag`
   - `test_candidate_ablation_changes_influence`
   - `test_epoch_tombstone_masks_current_authority_but_preserves_history`
   - `test_single_token_verdict_assertion`
   - `test_null_jlens_probe_interface`
   - `test_metrics_json_schema`
   - `test_result_card_generation`

10. Final verification commands:
    Run and confirm exit 0:
    - `python3 -m unittest discover -s tests`
    - `python3 -m compileall broadcast_alpha tests`
    - `python3 -m broadcast_alpha run-synthetic --seed 42`
    - `python3 -m broadcast_alpha summarize artifacts/<run_id>`
    - `python3 -m broadcast_alpha replay artifacts/<run_id> --agent agent_1 --step 3`
    - `python3 -m broadcast_alpha export-ledger artifacts/<run_id> --format jsonl`
    - `git diff --check`
    - `git status --short --branch`

SCOPE:
Modify only within the Git-backed app repo unless explicitly updating the
workspace-level progress docs:
- `/Volumes/WS4TB/claswarmed/claswarmed-app/README.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/pyproject.toml`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/broadcast_alpha/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/tests/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/prereg/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/docs/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/FAILURE_LEDGER.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/.gitignore`
- Generated run artifacts under `/Volumes/WS4TB/claswarmed/claswarmed-app/artifacts/`

Read/reference:
- `/Volumes/WS4TB/claswarmed/HANDOFF_claswarmed_glassgate_v1_2.md`
- `/Volumes/WS4TB/claswarmed/AMENDMENT_1-1_glassgate_codex_merge.md`
- `/Volumes/WS4TB/claswarmed/BROADCAST_ALPHA_CODEX_HANDOFF.md`
- `/Volumes/WS4TB/claswarmed/2606.26294v2.pdf`
- `/Volumes/WS4TB/claswarmed/swarm-code/`
- Current `claswarmed/` package for continuity only.

Do not modify unless explicitly approved:
- `/Volumes/WS4TB/claswarmed/swarm-code/`
- `/Volumes/WS4TB/claswarmed/openscience/`
- `/Volumes/WS4TB/claswarmed/gateway/`
- `/Volumes/WS4TB/claswarmed/hyperbrowser-app-examples/`
- `/Volumes/WS4TB/codxswarm/CAM_CAM/`
- `/Volumes/WS4TB/codxswarm/CAM_Codx/`

CONSTRAINTS:
- Build a falsification instrument, not a generic product.
- The number is the demo. Prioritize metrics, replay, and kill criteria over UI.
- Discrimination is primary: correct-minority influence minus
  incorrect-minority influence.
- Influence must be based on final success and/or candidate-level ablation, not
  mere workspace presence.
- Always include abundant, random, scarce_naive_topk, and scarce_protected arms
  before claiming anything about scarce broadcast governance.
- No LLM/API spend before synthetic discrimination, replay, random gate, and
  result-card tests pass.
- Do not add heavy orchestration frameworks. Python stdlib + SQLite are the
  default for macro rails. Use extra dependencies only when required and
  justified in `DECISIONS.md` or equivalent.
- Do not compare local models to frontier models unless layer access,
  finetuning, or representation manipulation is the tested variable.
- Do not make clinical, consciousness, AGI, or civilization-scale claims in the
  product docs. Keep those as motivation, not result claims.
- Negative results must be preserved, not routed around.
- Do not delete ledger records. Tombstone authority instead.
- Do not weaken or remove tests to pass.

SAFETY / PROVENANCE:
- Every experiment requires a committed prereg file before the run.
- Every run writes metrics, result card, replay bundle, and ledger export.
- Every failed claim or kill criterion is recorded in `FAILURE_LEDGER.md`.
- Keep implemented behavior separate from future rails.
- Cite external papers/repos before implementing real interpretability methods.
- Prefer explicit uncertainty over fake completeness.

ITERATION:
Work in small, gated batches:

1. Phase 0A: repo skeleton, docs, failure ledger, prereg stubs.
2. Phase 1: contracts, append-only ledger, verification, replay.
3. Phase 2a: synthetic deterministic harness, formulas, gates, result cards.
4. Phase 0B parallel: NullJLensProbe, single-token checks, source lookup for
   real J-lens.
5. Phase 2b: macro 24-cell DSH grid only after Phase 2a passes.
6. Phase 3: RQGM epoch manager and tombstoning.
7. Phase 4/5: Glass Gate bridge and mechanistic admission only if J-lens rail
   remains alive.
8. Phase 6: result-table and write-up scaffolding.

After each phase:
- run nearest tests;
- inspect artifacts;
- update `FAILURE_LEDGER.md` if a claim dies;
- commit with a claim ID in the message where applicable;
- push to `origin/main` only after tests pass.

STOP:
Pause and report if:
- the checkpoint tag is missing or local repo state is ambiguous;
- the same verification failure persists after 3 distinct repair attempts;
- a required external source for real J-lens cannot be identified;
- white-box model access is unavailable for Glass Gate rails;
- API/model spend is required before synthetic rails pass;
- task-bank size prevents the preregistered 24-cell minimum grid;
- implementation would require modifying protected source repos;
- a kill criterion fires for a rail;
- the work would become a generic orchestrator/product instead of the
  falsification instrument.

COMPLETE:
This goal is complete only when the app can produce, unattended:

1. `GLASSGATE_LIFT` with 95% CI.
2. D estimates for the macro grid arms.
3. Replayable, tamper-evident ledger for each run.
4. Seed detectability audit.
5. Epoch trajectory under evaluator evolution.
6. Result card and metrics JSON for every run.
7. If the J-lens rail survives source/model gating, PC-D relationship and at
   least one causal intervention result; otherwise, a clean failure/defer record.
8. Clean Git state, pushed commits, and final changed-file summary with exact
   verification command results.
```

## Assumptions

- The Git-backed implementation target remains
  `/Volumes/WS4TB/claswarmed/claswarmed-app`.
- The existing `claswarmed/` package may remain as a compatibility/demo layer,
  but the primary instrument package should be `broadcast_alpha/`.
- The J-lens source is not yet verified. A real J-lens rail must begin with
  source discovery and citation; otherwise only `NullJLensProbe` is in scope.
- The first credible value milestone is the synthetic end-to-end harness plus
  result card. The full v1.2 claim requires the macro grid and replayable
  metrics.

## Smaller Test-Run Goal

If a full v1.2 run is too broad for the next session, use this smaller goal:

```text
/goal
OUTCOME: Implement Phase 0A, Phase 1, and Phase 2a only: repo skeleton,
prereg stubs, failure ledger, append-only ledger, replay, synthetic
deterministic harness, D/GLASSGATE_LIFT metrics, and result cards.

PROOF OF DONE:
- `python3 -m unittest discover -s tests` exits 0.
- `python3 -m compileall broadcast_alpha tests` exits 0.
- `python3 -m broadcast_alpha run-synthetic --seed 42` creates one artifact
  with `metrics.json`, `result_card.md`, ledger export, and replay bundle.
- Tamper test fails chain verification after modifying a receipt.
- `git diff --check` is clean.

STOP: Do not use LLM/API tokens, do not implement real J-lens, and do not start
the live 24-cell macro grid in this smaller goal.
```
