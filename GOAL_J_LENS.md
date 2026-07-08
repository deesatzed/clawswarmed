# GOAL_J_LENS.md

Use this as the next Codex `/goal` for reopening the Glass Gate J-lens rail.

```text
/goal

OUTCOME:
Reopen the currently frozen J-lens / Glass Gate rail in `clawswarmed` by
turning `JLENS-FREEZE-001` from a justified defer record into either:

1. a verified real white-box J-lens probe artifact with causal intervention
   controls, or
2. a stronger explicit kill/defer record proving why the real probe cannot run
   yet.

The goal is not merely to install a dependency or render a visualization. The
goal is to establish whether outcome leakage creates an early verdict-direction
representation in a white-box gatekeeper before evidence is processed, and
whether intervening on that representation changes downstream adjudication.

RAW IDEA:
The previous Glass Gate build proved the macro DSH/RQGM/live-sweep rails but
kept J-lens, bridge, and mechanistic-admission rails deferred because the exact
source and white-box model access were missing. Anthropic's `jacobian-lens`
repository now appears to provide the exact reference implementation for the
global-workspace/Jacobian-lens method, and Neuronpedia may provide a no-code
sanity-check surface. Use those to reopen the rail honestly.

TASK TYPE:
Research/audit + optional dependency integration + white-box model experiment +
safety/provenance instrumentation.

CURRENT STARTING POINT:
- Workspace container: `/Volumes/WS4TB/claswarmed`
- Git-backed app repo: `/Volumes/WS4TB/claswarmed/claswarmed-app`
- Remote: `https://github.com/deesatzed/clawswarmed.git`
- Current app status before this goal was created:
  - latest pushed commit: `1a5c185 feat(live): add bounded model sweep`
  - `audit-goal` reported `overall_status = complete_with_deferred_records`
  - deferred requirement IDs: `jlens_or_clean_defer`, `bridge_rail`,
    `mechanistic_admission`
- Current freeze record:
  - `claswarmed-app/FAILURE_LEDGER.md`
  - `JLENS-FREEZE-001`
  - current reason: exact J-lens source and white-box model access unavailable
- Existing J-lens files:
  - `claswarmed-app/broadcast_alpha/jlens.py`
  - `claswarmed-app/docs/JLENS_SOURCE_GATE.md`
  - `claswarmed-app/prereg/PREREG_LEAK-01.md`
  - `claswarmed-app/prereg/PREREG_MECHADMIT-01.md`
  - `claswarmed-app/artifacts/jlens_gate_seed_42/`

CURRENT 2026-07-08 UPDATE:
- Exact source blocker is resolved.
  - `https://github.com/anthropics/jacobian-lens`
  - `https://transformer-circuits.pub/2026/workspace/index.html`
  - repo commit verified by `git ls-remote`:
    `581d398613e5602a5af361e1c34d3a92ea82ba8e`
- `JLENS-FREEZE-001` remains active as a runtime/model/intervention defer, not
  as a source-missing defer.
- New checked-in first-step artifacts:
  - `claswarmed-app/docs/JLENS_REOPEN_PACKET.md`
  - `claswarmed-app/docs/JLENS_MANUAL_SANITY_TEMPLATE.md`
  - `claswarmed-app/prereg/jlens_vignette_packet_01.json`
- Do not repeat source lookup unless checking for upstream source drift. The
  next implementation gate is a local white-box runtime smoke with a selected
  open-weight model and tokenizer-specific label validation.
- Runtime-readiness command added:
  `python3 -m broadcast_alpha prepare-jlens-probe --seed 42 --model-id hf-internal-testing/tiny-random-gpt2 --model-source huggingface`
- Current readiness artifact:
  `claswarmed-app/artifacts/jlens_runtime_readiness_seed_42/`
- Current readiness status: `blocked_missing_dependencies`.
  - `torch_missing`
  - `transformers_missing`
  - `jacobian_lens_reference_missing`
  - `tokenizer_label_check_incomplete`
- The next true progress step is to install/clone the reference implementation
  and white-box dependencies in an external runtime path, then rerun
  tokenizer-specific label checks and a tiny fit/apply smoke. Do not mark the
  J-lens rail proved from readiness alone.
- External runtime path created:
  - `external/jlens-runtime/jacobian-lens`
  - `external/jlens-runtime/.venv`
- Reference repo installed editable in the external venv and smoke-tested at
  commit `581d398613e5602a5af361e1c34d3a92ea82ba8e`.
- `run-jlens-smoke` added and current smoke artifact passed:
  `claswarmed-app/artifacts/jlens_smoke_seed_42/`
  - model: `reference_tiny_decoder`
  - model source/license: local reference, Apache-2.0
  - `torch`: 2.11.0
  - `numpy`: 2.4.4
  - `transformers`: 5.12.1
  - gradient/layer access confirmed for the reference tiny decoder
  - not an outcome-leak probe, not causal, not sufficient for `JLENS_PROVED`
- `run-jlens-hf-smoke` added and current Hugging Face smoke artifact passed:
  `claswarmed-app/artifacts/jlens_hf_smoke_seed_42/`
  - model: `hf-internal-testing/tiny-random-gpt2`
  - model source/license: Hugging Face, `unknown_not_declared`
  - model revision: `71034c5d8bde858ff824298bdedc65515b97d2b9`
  - model type/class: `gpt2`, `GPT2LMHeadModel`
  - tokenizer class: `GPT2Tokenizer`
  - layers/d_model: 5 layers, 32 hidden size
  - selected labels such as `" A"` and `" B"` are single tokens
  - earlier human-readable labels `yes`, `no`, `admit`, `reject`, `pass`,
    and `fail` are not all single tokens under this tokenizer
  - gradient/layer access confirmed for the tiny HF decoder
  - not an outcome-leak probe, not causal, not sufficient for `JLENS_PROVED`
- `run-jlens-leak-probe` added and current Hugging Face outcome-leak readout
  artifact passed as an execution artifact:
  `claswarmed-app/artifacts/jlens_leak_probe_seed_42/`
  - model: `hf-internal-testing/tiny-random-gpt2`
  - model revision: `71034c5d8bde858ff824298bdedc65515b97d2b9`
  - labels: tokenizer-verified `" A"` / `" B"` with `" Y"` / `" N"` sham
    readout labels
  - PC metric: `0.07183928849796455`
  - PC threshold: `1.0`
  - differential activation present: `false`
  - negative control performed: `true`
  - sham readout control performed: `true`
  - causal intervention performed: `false`
  - not causal, not sufficient for `JLENS_PROVED`
- `run-jlens-intervention` added and current intervention gate artifact
  executed:
  `claswarmed-app/artifacts/jlens_intervention_seed_42/`
  - intervention status: `blocked_no_differential_signal`
  - source PC metric: `0.07183928849796455`
  - source PC threshold: `1.0`
  - causal intervention performed: `false`
  - sham intervention control performed: `false`
  - derived `causal_support_set` entries: `2`
  - derived `convergence_dynamics` cases: `2`
  - derived metrics evidence classes:
    `shadow_probe_noninterventional` and `derived_readout_dynamics`
  - derived metrics are explicitly non-causal and not sufficient for
    `JLENS_PROVED`
  - decision: do not run causal intervention because the preregistered signal
    gate failed
  - not causal, not sufficient for `JLENS_PROVED`
- The next true progress step is a larger/better white-box model leak probe or
  a final clean defer decision. The current tiny-HF result preserves the freeze
  and blocks bridge/mechanistic-admission rails.

FIRST REQUIRED STEP:
Before editing, verify the current repo and baseline:

cd /Volumes/WS4TB/claswarmed/claswarmed-app
git status --short --branch
git log -1 --oneline
python3 -m unittest discover -s tests
python3 -m compileall -q broadcast_alpha tests
python3 -m broadcast_alpha summarize artifacts/goal_audit_seed_42

If the app repo is dirty, the current branch is not `main`, the baseline tests
fail, or `goal_audit_seed_42` is missing, stop and report before changing code.

PROOF OF DONE:
1. Source reopening:
   - Verify the exact external source from primary pages, not memory:
     `https://github.com/anthropics/jacobian-lens`
     and the linked global-workspace/Jacobian-lens paper.
   - Record source title, URL, license, commit SHA, and date accessed in a
     checked-in source manifest.
   - Update `docs/JLENS_SOURCE_GATE.md` so it no longer says the exact source
     is unverified if the source is verified.
   - Preserve the old freeze history in `FAILURE_LEDGER.md`; do not delete it.
   - Status: completed for the source-only slice on 2026-07-08. The rail is
     still frozen until white-box runtime and causal controls exist.

2. No-code sanity check:
   - Create a checked-in vignette packet with at least two paired prompts:
     outcome withheld and outcome revealed.
   - Include expected verdict labels and single-token label checks.
   - If a manual Neuronpedia/J-lens check is performed, record only a manual
     observation artifact with date, model/page shown, screenshots or exported
     text if available, and limitations.
   - Do not treat manual Neuronpedia inspection as formal proof.

2a. Optional black-box self-report companion probe:
   - Adapt, but do not directly adopt as evidence, the local skill at:
     `/Volumes/WS4TB/claswarmed/skirano-skills/skills/j-space-lens/`.
   - Treat this as a structured self-report protocol for black-box models, not
     as activation measurement, J-lens, Jacobian evidence, or causal evidence.
   - If implemented, create an artifact family such as
     `black_box_self_report_probe` with:
     - `evidence_class = behavioral_self_report`;
     - `not_activation_measurement = true`;
     - `not_causal = true`;
     - `not_sufficient_for_JLENS_PROVED = true`.
   - Use it only to compare what a model claims was active against later
     white-box J-lens readouts from an open-weight model.
   - Do not require self-report readouts on every normal Codex response. If a
     readout mode is used, keep it local to a bounded probe run.
   - Convert any "silent assessments" or "intermediate reasoning" language into
     brief observable self-report fields; do not request hidden chain-of-thought
     disclosure.

3. White-box runtime spike:
   - Use an open-weight or otherwise white-box-accessible Hugging Face decoder
     model with PyTorch gradient/layer access.
   - Do not use OpenRouter, Claude API, Gemini API, Grok API, or any black-box
     provider for the actual J-lens probe.
   - Clone or install `anthropics/jacobian-lens` in an external scratch area or
     optional dependency path. Do not vendor third-party source into the app repo
     unless license/provenance is explicitly documented and justified.
   - Record model ID, weight source, tokenizer, model license if available,
     hardware used, dtype, precision, dependency versions, and whether gradient
     access was confirmed.
   - Run the smallest possible fit/apply smoke with a tiny prompt set before
     touching the main app integration.
   - Status: first readiness command completed on 2026-07-08. It records the
     selected placeholder HF model and local dependency blockers, but does not
     install dependencies, load weights, confirm gradients, or run J-lens.
   - Status: external reference smoke completed on 2026-07-08. It confirms the
     cloned reference implementation can fit and apply a Jacobian lens on the
     repo's CPU-only tiny decoder. It does not satisfy outcome-leak or causal
     requirements.
   - Status: external Hugging Face smoke completed on 2026-07-08. It confirms a
     locally cached tiny HF decoder can be loaded, tokenized, fit, and applied
     through `anthropics/jacobian-lens` with gradient/layer access. It remains a
     smoke artifact only, not an outcome-leak or causal artifact.
   - Status: external Hugging Face outcome-leak readout probe completed on
     2026-07-08. It records pre-evidence A/B verdict-direction readouts for the
     paired vignettes, but PC is below threshold and no causal intervention was
     performed.
   - Status: intervention gate completed on 2026-07-08. It records that causal
     intervention was not run because the prerequisite differential signal was
     absent.
   - Status: derived shadow-probe fields added on 2026-07-08. The intervention
     artifact now records candidate support-set rows and convergence-dynamics
     summaries from the existing readouts. These fields are non-interventional,
     non-causal, and cannot satisfy the proof requirement.

4. App integration:
   - Add a real J-lens rail beside the existing `NullJLensProbe`; keep the null
     path available for unsupported environments.
   - Add CLI commands or subcommands that make the rail auditable, for example:
     `prepare-jlens-probe`, `run-jlens-smoke`, `run-jlens-leak-probe`, and
     `run-jlens-intervention`, or equivalent names consistent with the repo.
   - Every command must write:
     `metrics.json`, `result_card.md`, `ledger.jsonl`, `replay/contexts.json`,
     and any source/model manifests needed to reproduce the run.
   - Update `build-report`, `run-all`, and `audit-goal` only after the artifacts
     have tests and are truthfully interpreted.
   - Status: `prepare-jlens-probe` is implemented and integrated into
     `build-report`, `run-all`, and `audit-goal`; this was the first readiness
     gate before real smoke/leak/intervention commands were added.
   - Status: `run-jlens-smoke` and `run-jlens-hf-smoke` are implemented and
     integrated into `build-report` and `run-all`.
   - Status: `run-jlens-leak-probe` is implemented and integrated into
     `build-report`, `run-all`, and `audit-goal`.
   - Status: `run-jlens-intervention` is implemented and integrated into
     `build-report`, `run-all`, and `audit-goal`; it currently records a
     blocked/no-signal defer rather than a causal intervention.

5. C-MICRO-1 outcome-leak probe:
   - Update `PREREG_LEAK-01.md` before running the probe.
   - Run paired outcome-withheld and outcome-revealed vignettes through the
     white-box gatekeeper.
   - Export layer/position readouts for verdict-direction labels.
   - Compute and record premature convergence (`PC`) or the nearest explicitly
     defined preregistered metric.
   - Include negative controls and sham controls.
   - If no differential activation appears, keep or strengthen the J-lens
     freeze and stop the bridge/mechanistic rails.
   - Status: first tiny-HF execution completed on 2026-07-08 with PC
     `0.07183928849796455` below threshold `1.0`; this is a null pilot and the
     freeze remains active.

6. Causal intervention:
   - Do not claim causal prejudgment from timing/readout alone.
   - Implement at least one intervention comparison:
     ablation, swap, suppression, or equivalent mechanistic intervention.
   - Include a sham-control comparison.
   - Record whether the intervention changes downstream verdict/admission.
   - If intervention does not change outcome, report the result as null or
     negative; do not route around it.
   - Status: intervention gate completed on 2026-07-08 with
     `blocked_no_differential_signal`; no causal intervention was run because
     the leak probe did not meet the preregistered signal threshold.

6a. Optional derived J-space measurement fields from `jlens_ideas`:
   - Adapt only the ideas that strengthen current proof artifacts without
     expanding the v1 goal into speculative training, grafting, cross-modal, or
     generative-search rails.
   - `causal_support_set` / `shadow_probe`:
     - For each tested concept direction, record intervention type, layer,
       position, output/logit delta, verdict flip status, and sham-control
       comparison.
     - Use this to make the required causal intervention more inspectable, not
       to replace it.
     - Status: implemented as `shadow_probe_noninterventional` entries inside
       `artifacts/jlens_intervention_seed_42/metrics.json`, with
       `causal_intervention_performed = false`, `output_logit_delta = null`,
       and `not_sufficient_for_JLENS_PROVED = true`.
   - `convergence_dynamics`:
     - Optionally record entropy over layers, commitment/order parameter,
       collapse layer, and whether collapse occurred before the evidence span
       was processed.
     - Treat these as triage or suspicious-run flags only. They are not causal
       evidence without intervention.
     - Status: implemented as `derived_readout_dynamics` summaries inside
       `artifacts/jlens_intervention_seed_42/metrics.json`; current collapse
       layer is `null` for both checked-in cases.
   - `mechanistic_drift_rate`:
     - For future RQGM/evaluator epochs, optionally record cosine-distance
       drift of critical verdict directions such as `admit`, `reject`, `pass`,
       and `fail` across evaluator versions.
     - Treat this as an early-warning/tombstone candidate signal, not an
       automatic replacement or deletion rule.
   - Leave these `jlens_ideas` concepts deferred unless they can be attached to
     concrete artifacts, tests, and kill criteria:
     blind-spot cartography, time-travel debugging, concept archaeology,
     pressure/congestion stress, negative-space tuning, orthogonalization,
     cognitive grafting, controlled hallucination, cross-modal translation, and
     any training-heavy rail.

7. Bridge and mechanistic admission gates:
   - Reopen `PREREG_BRIDGE-01.md` and `PREREG_MECHADMIT-01.md` only if the
     J-lens rail survives source/model/probe/intervention gating.
   - If J-lens remains frozen or only produces non-causal readouts, keep bridge
     and mechanistic admission deferred with an explicit record.

8. Tests:
   Add or update tests equivalent to:
   - source manifest records exact source URL/license/SHA/date accessed;
   - black-box API models are rejected for real J-lens execution;
   - open-weight white-box model config is required before real probe;
   - black-box self-report artifacts, if implemented, are labeled non-proof and
     cannot satisfy the J-lens requirement;
   - single-token labels are verified against the selected tokenizer, not only
     whitespace;
   - null probe remains available and does not claim real evidence;
   - real/smoke probe writes all required artifacts;
   - causal claim is blocked unless intervention and sham-control evidence are
     present;
   - optional `causal_support_set`, `convergence_dynamics`, and
     `mechanistic_drift_rate` fields, if present, are labeled as derived metrics
     and cannot satisfy the J-lens causal proof requirement by themselves;
   - `audit-goal` distinguishes proved J-lens, deferred J-lens, and failed
     J-lens.

9. Final verification:
   Run and confirm exit 0, or record a blocking reason:
   - `python3 -m unittest discover -s tests`
   - `python3 -m compileall -q broadcast_alpha tests`
   - `python3 -m broadcast_alpha run-jlens-gate --seed 42`
   - the implemented J-lens smoke command
   - the implemented J-lens HF smoke command
   - the implemented leak-probe command, if hardware/dependencies allow
   - the implemented intervention command, if the leak probe survives
   - `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
   - `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
   - `python3 -m broadcast_alpha export-ledger artifacts/<new_jlens_artifact> --format jsonl`
   - `git diff --check`
   - `git status --short --branch`

SCOPE:
Modify only within the Git-backed app repo unless explicitly updating
workspace-level truth docs:
- `/Volumes/WS4TB/claswarmed/claswarmed-app/README.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/pyproject.toml`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/broadcast_alpha/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/tests/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/prereg/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/docs/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/FAILURE_LEDGER.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/artifacts/`

Allowed workspace-level truth docs:
- `/Volumes/WS4TB/claswarmed/GOAL_J_LENS.md`
- `/Volumes/WS4TB/claswarmed/PROGRESS.md`
- `/Volumes/WS4TB/claswarmed/DECISIONS.md`

Read/reference:
- `/Volumes/WS4TB/claswarmed/GOAL_GLASSGATE.md`
- `/Volumes/WS4TB/claswarmed/HANDOFF_claswarmed_glassgate_v1_2.md`
- `/Volumes/WS4TB/claswarmed/HANDOFF_claswarmed_glassgate.md`
- `/Volumes/WS4TB/claswarmed/AMENDMENT_1-1_glassgate_codex_merge.md`
- `/Volumes/WS4TB/claswarmed/BROADCAST_ALPHA_CODEX_HANDOFF.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/docs/archive/`
- `/Volumes/WS4TB/claswarmed/skirano-skills/skills/j-space-lens/`
- `https://github.com/anthropics/jacobian-lens`
- `https://www.neuronpedia.org/jlens`

Do not modify unless explicitly approved:
- `/Volumes/WS4TB/claswarmed/swarm-code/`
- `/Volumes/WS4TB/claswarmed/openscience/`
- `/Volumes/WS4TB/claswarmed/gateway/`
- `/Volumes/WS4TB/claswarmed/hyperbrowser-app-examples/`
- `/Volumes/WS4TB/claswarmed/clininfo-gate/`
- `/Volumes/WS4TB/codxswarm/CAM_CAM/`
- `/Volumes/WS4TB/codxswarm/CAM_Codx/`

CONSTRAINTS:
- Do not claim a real J-lens result without gradient/layer access to the actual
  model being probed.
- Do not use black-box API responses as substitutes for J-lens internals.
- Do not use black-box self-report as proof of internal activations,
  verdict-direction representations, or causal mechanism.
- Do not compare local/open models to frontier models unless layer access,
  finetuning, or representation manipulation is the tested variable.
- Do not frame Neuronpedia screenshots or manual UI inspection as formal proof.
- Do not frame J-space self-report tables as formal proof.
- Do not frame entropy/collapse dynamics, drift rates, or causal-support
  summaries as proof unless the required intervention and sham-control evidence
  is also present.
- Do not claim causality from readout timing alone.
- Do not add heavy dependencies to the default install path. Put J-lens
  dependencies behind an optional extra, documented setup, or external runner
  unless there is a justified reason otherwise.
- Do not commit model weights, downloaded corpora, API keys, cache directories,
  or large generated tensors unless explicitly approved and size/provenance are
  documented.
- Do not weaken existing macro DSH, RQGM, live-sweep, ledger, replay, or audit
  tests.
- Negative/null results are acceptable and must be preserved.

SAFETY / PROVENANCE:
- This is an AI-safety/research instrument, not a clinical or production
  decision system.
- Do not use PHI, patient-specific medical cases, or clinical decision content
  in the J-lens probe.
- Use synthetic vignettes only.
- Every source, model, dataset, prompt set, and artifact must have provenance.
- Preserve `JLENS-FREEZE-001` history even if the rail reopens.
- If the probe fails, update `FAILURE_LEDGER.md` with the exact failure mode
  rather than softening the claim.

ITERATION:
Work in gated batches:

1. Baseline verification and repo-state check.
2. Source verification and docs/manifest update.
3. Vignette packet and optional Neuronpedia manual sanity artifact.
4. Optional black-box self-report companion probe, explicitly labeled non-proof.
5. External `jacobian-lens` spike outside the app's default runtime.
6. Minimal app integration behind an optional/deferred runtime gate.
7. J-lens smoke artifact with no causal claim.
8. Leak probe artifact with preregistered PC metric.
9. Causal intervention/sham-control artifact.
10. Optional derived metrics: causal support set, convergence dynamics, and
    mechanistic drift fields, if cheap and testable.
11. Report/audit integration.
12. Bridge/mechanistic-admission reopen decision.

After each batch:
- run the nearest relevant tests;
- inspect generated artifacts;
- update `PROGRESS.md`;
- update `DECISIONS.md` for dependency, model, hardware, or methodology
  choices;
- commit and push only after verification passes and no secrets/weights are
  staged.

STOP:
Pause and report if:
- the repo baseline is dirty or tests fail before editing;
- the exact source cannot be verified from primary pages;
- `anthropics/jacobian-lens` cannot be installed or imported in a controlled
  environment;
- no suitable white-box/open-weight model can be configured;
- selected labels are not single tokens under the selected tokenizer;
- hardware cannot run even the smallest smoke;
- dependency install requires unapproved network or large downloads;
- the same technical failure persists after 3 distinct repair attempts;
- the probe is flat or intervention controls do not support causality;
- any step risks committing secrets, PHI, model weights, or large caches;
- bridge/mechanistic admission would proceed without a live J-lens rail.
- a black-box self-report artifact is being treated as a substitute for
  white-box Jacobian/activation evidence.

COMPLETE:
Mark this goal complete only when one of these two outcomes is true:

A. Reopened/proved path:
- exact J-lens source is verified and cited;
- white-box model runtime is configured and recorded;
- smoke, leak-probe, and causal-intervention artifacts exist;
- ledgers verify;
- tests pass;
- `audit-goal` distinguishes the J-lens rail as proved or active according to
  the implemented evidence threshold;
- bridge/mechanistic admission are either reopened with prereg gates or
  explicitly left deferred for a documented reason.

B. Clean kill/defer path:
- exact source, dependency, model, hardware, or causal-intervention blocker is
  recorded in `FAILURE_LEDGER.md`;
- null/failed artifacts are replayable and ledgered where applicable;
- `audit-goal` still reports a clean deferred J-lens record, not an incomplete
  undocumented gap;
- tests pass;
- final summary clearly states what evidence was attempted and why the rail
  remains frozen.
```

## Assumptions

- The first implementation target remains
  `/Volumes/WS4TB/claswarmed/claswarmed-app`.
- The J-lens source to verify is currently expected to be
  `https://github.com/anthropics/jacobian-lens`, but the future goal runner
  must verify that from primary sources before implementation.
- The Neuronpedia page is useful only as a manual sanity check; it is not a
  substitute for local/reproducible white-box artifacts.
- The first model should be small enough for a local or modest cloud GPU smoke;
  model quality is secondary to gradient/layer access.
- OpenRouter/frontier API models remain useful for behavior-only live sweeps,
  but they cannot satisfy the real J-lens requirement.

## Smaller Test-Run Goal

If the full goal is too broad for one session, use this first:

```text
/goal
OUTCOME:
Produce only the J-lens reopen packet: source verification manifest, vignette
packet, Neuronpedia/manual-sanity artifact template, dependency/model decision
record, and updated `docs/JLENS_SOURCE_GATE.md`. Do not install heavy
dependencies or run a model.

PROOF OF DONE:
- `python3 -m unittest discover -s tests` exits 0.
- `python3 -m compileall -q broadcast_alpha tests` exits 0.
- Source manifest records exact URL, license, commit SHA/date accessed, and
  whether the source satisfies the prior gate.
- Vignette packet contains outcome-withheld and outcome-revealed pairs.
- `FAILURE_LEDGER.md` preserves `JLENS-FREEZE-001`.
- `git diff --check` is clean.

STOP:
Do not download model weights, run J-lens fitting, or reopen bridge/mechanistic
rails in this smaller goal.
```
