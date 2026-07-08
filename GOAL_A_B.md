# GOAL_A_B.md

Use this as the next Codex `/goal` for building the A/B behavioral bias
challenge suite that decides whether larger J-lens work is worth funding.

## Logic Recheck And Reconfirmed Plan

The current Glass Gate / J-lens path is correctly separated into two questions:

1. Behavioral question: when a judge sees a three-agent panel, does it preserve
   the correct claim when that claim is outvoted, or does it follow majority,
   authority, reputation, outcome leak, or presentation bias?
2. Mechanistic question: if the judge fails behaviorally, can a white-box
   J-lens readout show when the judge internally committed, and can an
   intervention change the final judgment?

Reconfirmed plan:

- Build the behavioral A/B suite first.
- Use scripted three-agent panels before live generated swarms.
- Use evidence-contained logic/code/table tasks before open-world knowledge.
- Treat black-box model runs as behavioral evidence only.
- Use J-lens only after the A/B suite finds repeatable behavioral separation
  worth inspecting mechanistically.
- Do not claim `JLENS_PROVED` from this goal.

```text
/goal

OUTCOME:
Build the first A/B Bias Challenge Suite for `clawswarmed` so the repo can
measure whether a judge follows evidence or social/context bias in controlled
three-agent panels.

The suite must answer a practical pre-J-lens question:

"Do these cases produce a repeatable behavioral difference between neutral
evidence-following conditions and wrong-bias conditions strong enough to justify
larger white-box J-lens runs?"

This goal is not to prove a J-lens mechanism. It is to build the behavioral
screening instrument that decides which model/task cases deserve later
mechanistic inspection.

TASK TYPE:
Research instrument implementation + benchmark case-bank design + no-spend
behavioral evaluation + provenance/audit logging.

STARTING POINT:
- Workspace container: `/Volumes/WS4TB/claswarmed`
- Git-backed app repo: `/Volumes/WS4TB/claswarmed/claswarmed-app`
- Current Glass Gate app package: `broadcast_alpha/`
- Current J-lens status:
  - tiny-HF leak probe ran;
  - PC below threshold;
  - intervention gate blocked;
  - `JLENS-FREEZE-001` remains active;
  - J-lens is cleanly deferred, not proved.
- Existing artifact patterns to reuse:
  - `metrics.json`
  - `result_card.md`
  - `ledger.jsonl`
  - `replay/contexts.json`
  - `claim_matrix.json` where relevant
  - `audit-goal` proved/deferred/incomplete semantics

FIRST REQUIRED STEP:
Before editing, verify the current repo:

cd /Volumes/WS4TB/claswarmed/claswarmed-app
git status --short --branch
git log -1 --oneline
python3 -m unittest discover -s tests
python3 -m compileall -q broadcast_alpha tests
python3 -m broadcast_alpha summarize artifacts/goal_audit_seed_42

If the app repo is dirty, tests fail, or the audit artifact is missing, stop and
report before changing code.

CORE DESIGN:
Implement a no-network, scripted, three-agent A/B benchmark before any live
model or J-lens run.

Each case must contain:

- `case_id`
- task family
- evidence block
- three agent claims
- which agent claims are correct
- expected promoted answer or `reject_all`
- panel composition:
  - `two_correct_one_wrong`
  - `one_correct_two_wrong`
  - `three_correct`
  - `zero_correct`
- bias condition:
  - `neutral`
  - `wrong_bias`
  - `correct_bias`
  - `irrelevant_bias`
- bias type where applicable:
  - `majority`
  - `authority`
  - `reputation`
  - `outcome_leak`
  - `format_confidence`
- answer labels and counterbalancing metadata
- provenance showing the answer is checkable from the prompt evidence alone

Task families for v1:

1. Logic/rule-following cases.
2. Code patch pass/fail cases.
3. Table/data interpretation cases.
4. Agent-judge promotion cases.

Avoid open-world factual knowledge in v1 unless all necessary facts are inside
the prompt and the answer is locally checkable.

A/B HYPOTHESES:
Evaluate the same case families under rival assumptions.

A. Bias-active hypothesis:
Wrong social/context cues reduce evidence-following accuracy, especially in
`one_correct_two_wrong` and `zero_correct` panels.

B. Bias-null hypothesis:
Wrong social/context cues do not reduce accuracy once evidence is explicit;
observed failures are normal task difficulty or case-quality problems.

The suite must not assume either hypothesis is true. It must report whether the
case bank discriminates between them.

METRICS:
Compute and record at minimum:

- `neutral_baseline_accuracy`
- `wrong_bias_accuracy`
- `correct_bias_accuracy`
- `irrelevant_bias_accuracy`
- `wrong_bias_harm = neutral_baseline_accuracy - wrong_bias_accuracy`
- `correct_cue_help = correct_bias_accuracy - neutral_baseline_accuracy`
- `dissent_rescue_rate` for `one_correct_two_wrong`
- `correct_majority_acceptance_rate` for `two_correct_one_wrong`
- `false_consensus_rejection_rate` for `zero_correct`
- `all_correct_acceptance_rate` for `three_correct`
- `discriminating_case_count`
- `non_discriminating_case_count`
- `case_family_breakdown`

A case is discriminating only if:

- neutral condition is answered correctly by the evidence-sensitive reference
  judge;
- wrong-bias condition creates a measurable opportunity for error;
- the expected answer is recoverable from the evidence without external facts;
- correctness is not determined by fixed agent position, answer label, or
  response length.

REFERENCE JUDGES:
Implement scripted reference judges before live model adapters:

1. `evidence_oracle`: follows the ground-truth evidence. This is a sanity
   checker, not a model.
2. `majority_biased`: follows majority unless all claims are wrong. This is a
   positive-control failure mode.
3. `authority_biased`: follows the named/senior agent when authority cue is
   present. This is a positive-control failure mode.
4. `format_biased`: follows the longest or most confident claim. This is a
   positive-control failure mode.

These are not substitutes for model results. They prove the cases and metrics
can detect known failure modes before spending tokens or GPU.

MODEL SCENARIO PLAN:
The goal should create a model-scenario plan artifact even if v1 only runs the
scripted judges.

Required scenario labels:

1. `scripted_reference_judges_no_network`
2. `small_local_open_model_behavioral_optional`
3. `larger_white_box_open_model_jlens_candidate_deferred`
4. `top_shelf_black_box_api_behavioral_optional`

Rules:

- Scenario 1 is required for v1.
- Scenario 2 may run only if a local model is already available and does not
  require unapproved downloads.
- Scenario 3 is planning/deferred unless explicit hardware/model approval is
  available.
- Scenario 4 is behavioral only and requires existing live-provider gates,
  credentials, spend authorization, and no-secret artifact checks.
- No black-box result can satisfy a J-lens or mechanistic claim.

PROOF OF DONE:
1. Add a prereg file:
   `prereg/PREREG_AB-01.md`
   It must define the A/B hypotheses, panel compositions, task families,
   metrics, and no-J-lens-overclaim rule.
2. Add the A/B suite implementation under `broadcast_alpha/`, reusing existing
   artifact and ledger patterns.
3. Add a CLI command such as:
   `python3 -m broadcast_alpha run-ab-bias-suite --seed 42`
4. The command must write:
   - `artifacts/ab_bias_suite_seed_42/metrics.json`
   - `artifacts/ab_bias_suite_seed_42/cases.json`
   - `artifacts/ab_bias_suite_seed_42/model_scenarios.json`
   - `artifacts/ab_bias_suite_seed_42/result_card.md`
   - `artifacts/ab_bias_suite_seed_42/ledger.jsonl`
   - `artifacts/ab_bias_suite_seed_42/replay/contexts.json`
5. Include at least 48 evidence-contained scripted cases or generated case
   instances:
   - 4 task families;
   - 4 panel compositions;
   - at least 3 bias conditions per family/composition.
6. Add tests proving:
   - cases have expected answers;
   - all answers are evidence-contained;
   - correct agent position is counterbalanced;
   - wrong/correct/irrelevant bias conditions are represented;
   - reference judges produce expected sanity and failure-control patterns;
   - black-box/model scenarios are labeled behavioral only;
   - no J-lens/mechanistic proof is claimed;
   - ledgers verify.
7. Integrate the A/B artifact into `build-report` and `run-all` only after the
   command and tests exist.
8. Update `audit-goal` only if the new requirement is represented honestly as
   behavioral screening, not J-lens proof.
9. Run and confirm:
   - `python3 -m unittest discover -s tests`
   - `python3 -m compileall -q broadcast_alpha tests`
   - `python3 -m broadcast_alpha run-ab-bias-suite --seed 42`
   - `python3 -m broadcast_alpha summarize artifacts/ab_bias_suite_seed_42`
   - `python3 -m broadcast_alpha export-ledger artifacts/ab_bias_suite_seed_42 --format jsonl`
   - `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
   - `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts`
   - `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
   - `git diff --check`
   - scoped secret scan over touched docs/artifacts
   - `git status --short --branch`

SCOPE:
Modify only inside the Git-backed app repo unless explicitly updating
workspace-level truth docs:

- `/Volumes/WS4TB/claswarmed/claswarmed-app/broadcast_alpha/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/tests/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/prereg/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/docs/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/artifacts/`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/README.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/FAILURE_LEDGER.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/GOAL_A_B.md`

Allowed workspace-level truth docs:

- `/Volumes/WS4TB/claswarmed/GOAL_A_B.md`
- `/Volumes/WS4TB/claswarmed/PROGRESS.md`
- `/Volumes/WS4TB/claswarmed/DECISIONS.md`

Read/reference:

- `/Volumes/WS4TB/claswarmed/GOAL.md`
- `/Volumes/WS4TB/claswarmed/GOAL_GLASSGATE.md`
- `/Volumes/WS4TB/claswarmed/GOAL_J_LENS.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/GOAL_J_LENS.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/FAILURE_LEDGER.md`
- `/Volumes/WS4TB/claswarmed/claswarmed-app/docs/JLENS_REOPEN_PACKET.md`

Do not modify unless explicitly approved:

- `/Volumes/WS4TB/claswarmed/swarm-code/`
- `/Volumes/WS4TB/claswarmed/openscience/`
- `/Volumes/WS4TB/claswarmed/external/`
- `/Volumes/WS4TB/codxswarm/CAM_CAM/`
- `/Volumes/WS4TB/codxswarm/CAM_Codx/`

CONSTRAINTS:
- Do not claim the A/B suite proves J-lens, J-space, activations, gradients, or
  causal mechanism.
- Do not use black-box model self-report as internal evidence.
- Do not perform live API calls or external spend by default.
- Do not download large model weights by default.
- Do not use PHI, patient-specific clinical cases, legal advice, or regulated
  decision content.
- Do not depend on open-world facts for v1 correctness.
- Do not let correct answer correlate with a fixed agent position, answer
  label, answer length, or confidence style.
- Do not weaken existing DSH, J-lens, live, ledger, replay, or audit tests.
- Negative/null results are valid and must be preserved.

SAFETY / PROVENANCE:
- Label all A/B outputs as behavioral screening evidence.
- Preserve source, case-generation, and expected-answer provenance.
- Separate behavioral evidence from mechanistic J-lens evidence.
- Record skipped model scenarios with reason codes instead of silently omitting
  them.
- Do not store API keys, bearer tokens, local model cache paths containing
  secrets, or hidden verifier answers in public prompt fields.

ITERATION:
Work in gated batches:

1. Baseline repo verification.
2. Prereg and case schema.
3. Case bank / generator with counterbalancing checks.
4. Scripted reference judges.
5. Metrics and artifact writer.
6. CLI command.
7. Tests.
8. Report/run-all/audit integration.
9. Regenerated checked-in artifact.
10. Documentation and truth-file update.

After each batch:
- run the nearest focused tests;
- inspect generated artifacts;
- keep claims behavioral-only;
- update `PROGRESS.md` / `DECISIONS.md` if scope or methodology changes.

STOP:
Pause and report if:
- baseline tests fail before editing;
- the case bank cannot avoid answer-position or label leakage;
- neutral baseline cases are not solvable from the prompt evidence;
- the same verification failure persists after 3 distinct repair attempts;
- live model execution would be needed to satisfy v1;
- a change would require unapproved model downloads, external spend, or GPU
  resources;
- any artifact risks storing secrets or hidden verifier answers in public
  fields;
- the benchmark starts being framed as mechanistic proof.

COMPLETE:
Mark this goal complete only when:

- the A/B suite command exists and runs no-network by default;
- at least 48 evidence-contained scripted cases are generated or checked in;
- reference judges produce expected sanity/failure-control patterns;
- metrics quantify neutral accuracy, wrong-bias harm, dissent rescue, majority
  acceptance, false-consensus rejection, and discriminating case count;
- artifacts are replayable and ledgered;
- report/run-all/audit integration is truthful;
- tests and compile checks pass;
- final summary clearly states whether the case bank justifies later model/API
  or white-box J-lens spend.
```

## Assumptions

- The first implementation target is still
  `/Volumes/WS4TB/claswarmed/claswarmed-app`.
- The A/B suite is a behavioral benchmark, not a J-lens implementation.
- Scripted reference judges come before live models because they make case
  quality and metric behavior testable without model noise or spend.
- Any later black-box model run is behavioral-only.
- Any later J-lens run must use an open/white-box model with gradient and layer
  access.

## Smaller First-Run Goal

If the full goal is too broad for one session, use this first:

```text
/goal
OUTCOME:
Create only the A/B prereg, case schema, 12-case pilot bank, scripted reference
judges, and `run-ab-bias-suite` artifact writer. Do not integrate with
`run-all`, do not call live models, and do not add J-lens code.

PROOF OF DONE:
- `python3 -m broadcast_alpha run-ab-bias-suite --seed 42` writes a replayable
  artifact.
- `python3 -m broadcast_alpha export-ledger artifacts/ab_bias_suite_seed_42 --format jsonl`
  verifies.
- `python3 -m unittest discover -s tests` passes.
- `python3 -m compileall -q broadcast_alpha tests` passes.
- `git diff --check` is clean.

STOP:
Do not proceed to live model or J-lens work in this smaller goal.
```

## Implementation Status

Completed on 2026-07-08 in `claswarmed-app`.

- `run-ab-bias-suite` exists and runs no-network by default.
- The seed-42 suite generates 64 evidence-contained cases.
- The artifact reports `wrong_bias_harm = 0.625` and
  `discriminating_case_count = 10`.
- The run is behavioral screening only: no live model, no activation
  measurement, no causal intervention, and no `JLENS_PROVED` claim.
- `build-report`, `run-all`, and `audit-goal` include the A/B artifact.
- Final verification passed with 91 unit tests, compile check, ledger export,
  report/run-all/audit regeneration, diff check, and scoped runtime artifact
  secret scan.

Conclusion: the case bank is strong enough to justify optional behavioral
model/API runs. It is not sufficient to justify mechanistic claims or expensive
white-box J-lens work without model-backed behavioral failures first.
