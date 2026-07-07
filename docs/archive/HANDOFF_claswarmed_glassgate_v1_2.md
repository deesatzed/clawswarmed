# HANDOFF: claswarmed / Broadcast-alpha / Glass Gate v1.2

**A research instrument for measuring whether AI-team communication preserves or destroys correct minority signal, with a mechanistically audited gatekeeper.**

**Version:** 1.2  
**Date:** 2026-07-07  
**Owner:** Wayne Satz / deesatzed  
**Builder:** Codex / Claude Code  
**Canonical status:** This document supersedes `HANDOFF_claswarmed_glassgate.md` v1.0 and incorporates `AMENDMENT_1-1_glassgate_codex_merge.md`. Keep prior docs in `docs/archive/`, but build from this file.

---

## 0. The plain-English artifact

At the end, you will have a piece of software that runs a rigged, reproducible experiment hundreds of times.

The rig:

1. A team of AI agents works on a problem with a checkable right answer.
2. One agent is secretly given the critical correct insight, while the majority receives plausible but wrong or incomplete information.
3. In matched runs, one agent is instead given a plausible but wrong minority insight.
4. The system varies only how information is shared:
   - everyone sees everything;
   - a random k-slot board admits candidates;
   - a naive top-k gate admits candidates;
   - a protected scarce-broadcast gate admits candidates;
   - later, a mechanistically audited white-box Glass Gate admits candidates.
5. Every candidate, admission, rejection, evaluator score, epoch replacement, and final result is logged in a tamper-evident ledger.
6. Any run can be replayed exactly.
7. The software outputs one main result number.

The number is the demo:

```text
GLASSGATE_LIFT = D(scarce_protected) - max(D(abundant), D(random), D(scarce_naive_topk))
```

where:

```text
D(arm) = influence(correct_minority_seed) - influence(incorrect_minority_seed)
```

In plain language:

> When one agent is right and outvoted, does the team's communication structure rescue that insight or bury it, and does it rescue right dissent without also swallowing wrong dissent?

A positive `GLASSGATE_LIFT` says the protected scarce-broadcast structure preserved useful dissent better than the controls. A negative value says the design pattern is dangerous or at least unsupported. A value near zero says the governance gate did not add measurable value.

This instrument is not a product, not a model router, not a chat UI, not a clinical system, and not a consciousness claim. It is a falsification harness for one question.

---

## 1. Honest elevator version

> Teams of AIs are being deployed everywhere, and most of them share information like an unmoderated group chat. This instrument measures whether that is the right design. Specifically, it tests whether the communication structure protects or silences the one agent that is right when everyone else is wrong, and whether the AI that moderates the conversation can be caught pre-judging. The output is a number, a confidence interval, and a replayable ledger.

This is the README-level message. Do not let Codex turn it into a product pitch.

---

## 2. Why anyone would want it

### 2.1 Agent builders

Most multi-agent systems default to a shared transcript. That may be costly, noisy, and prone to manufactured consensus. This rig tests whether a small governed broadcast board beats the shared transcript, and whether naive scarcity suppresses the only correct minority signal.

Useful outcomes:

- protected scarcity beats abundant transcript: a design rule;
- naive scarcity suppresses correct dissent: a warning result;
- random k-slot admission matches protected admission: gate intelligence is not doing useful work;
- abundant transcript beats scarcity: the scarce-workspace thesis is weakened or killed.

Any of these is a result.

### 2.2 People worried about AI judges

The gatekeeper is not just another black-box judge. The Glass Gate must be a white-box model with gradient/layer access. We audit the adjudicator, not every agent. The J-lens rail tests whether the gatekeeper internally converged on a verdict before evidence was processed, and whether suppressing that early verdict direction changes downstream discrimination.

This is the AI-judge version of catching hindsight bias.

### 2.3 Research community

Two publishable candidates, without inflation:

1. An interpretability readout used as a criterion for replacing an AI evaluator under a Red-Queen/RQGM-style epoch process.
2. A tested bridge between what happens inside a gatekeeper model and what happens across a team of agents.

Neither is assumed. Both have kill criteria.

---

## 3. Codex operating contract

You are building a research instrument. Every phase must end in a run that can kill a claim.

Rules:

1. Do not add generic orchestrator features: no model marketplace, generic routing, agent chat UI, or convenience framework unless a preregistered rail requires it.
2. Every experiment gets a `prereg/PREREG_<ID>.md` committed before the run: hypothesis, conditions, primary metric, kill criterion, seed.
3. Every negative result goes into `FAILURE_LEDGER.md`.
4. Every commit references a claim ID, for example: `feat(gate): add random control arm [C-MACRO-1]`.
5. When a kill criterion fires, stop that rail and surface the result. Do not route around it.
6. Do not compare local models to frontier models unless layer access, finetuning, or representation manipulation is the variable being tested.
7. A white-box model means a model with gradient/layer access. It may be local or cloud-hosted.
8. Python stdlib + SQLite for the macro rail unless an approved dependency is listed below. J-lens rail may use PyTorch/HF Transformers.
9. No heavy orchestration frameworks unless explicitly approved.

---

## 4. Claim structure

### Parent claim

```text
Coordination quality in a multi-agent system is governed by what wins access to a scarce broadcast channel. The gate that controls access can become trustworthy only if it is reality-anchored, replayable, and mechanistically auditable. A transparent, epoch-evolving Glass Gate should preserve correct minority signal better than abundant sharing, random k-slot admission, and naive top-k scarcity.
```

### Rail claims

| ID | Rail | Claim | Kill criterion |
|---|---|---|---|
| C-MACRO-1 | Dissent survival | Scarce protected broadcast beats abundant transcript, random admission, and naive top-k on discrimination at matched panel correlation. | If scarce protected fails to beat all three controls on D or `GLASSGATE_LIFT <= 0`, the governance thesis is unsupported or dead. |
| C-MACRO-2 | Independence | Information partitioning yields more usable independence than shared-context correlated panels. | If partitioned panels show no D gain over correlated panels, the independence lever is weak or dead. |
| C-MACRO-3 | Mechanistic admission | J-space-derived admission features from white-box candidate-generating agents beat human-shaped scoring features on D at matched cost. | If mechanistic admission does not beat human-category admission, the pre-verbal/legibility-filter thesis remains unproven. |
| C-MICRO-1 | Outcome leak | Outcome leakage installs a verdict-direction representation in the gatekeeper's J-space before the evidence span is processed. | If the weekend probe shows no differential activation, pause the J-lens rail. |
| C-MICRO-2 | Causality | Early verdict representation is causal, not cosmetic. | If ablation/swap does not move final verdicts or D, hindsight scores are noise. |
| C-BRIDGE-1 | Micro-macro bridge | Gatekeepers with higher premature convergence produce lower macro discrimination; suppressing the premature direction raises D. | If PC does not correlate with D or intervention does not change D, the internal/external bridge is not supported. |
| C-RQGM-1 | Evolution | Epoch-based evaluator replacement anchored on hard outcomes plus mechanistic audit veto improves D without Goodhart collapse. | If D degrades, seed camouflage fails, or challengers game the anchors, co-evolution is unsafe here. |

---

## 5. Non-negotiable design principles

1. **The number is the demo.** Produce `GLASSGATE_LIFT`, D by arm, confidence intervals, and replay links.
2. **Discrimination, not mere survival.** Passing every dissent is as broken as passing none. Score correct-minority influence minus incorrect-minority influence.
3. **Influence, not presence.** Workspace presence is diagnostic only. Candidate-level ablation is primary for attribution.
4. **Isolate scarcity from governance.** Always include abundant, random, scarce-naive, and scarce-protected arms.
5. **Independence is engineered and measured.** Primary lever: disjoint information access. Report panel correlation rho on every run.
6. **Glass Gate.** Swarm agents may be black boxes. The scarce-protected/RQGM gatekeeper must be white-box with gradient/layer access once the Glass Gate rail is active.
7. **Reality anchors only.** v0 tasks must have hard external verification: hidden tests, formal checks, held-out facts, arithmetic, simulation, or proof checking.
8. **Erase authority, not record.** Use append-only ledger records. RQGM-style invalidation is epoch-scoped tombstoning: old scores remain historically replayable but are invalid for current ranking.
9. **J-lens timing is not causality.** Any J-lens claim requires intervention: ablation, swap, suppression, or sham-control comparison.
10. **Seed camouflage.** Seeded hints must not be trivially detectable as seeds.
11. **Human-readable views are renders, not substrate.** Canonical records are structured contracts. English is for audit/UI.
12. **Post-linguistic A2A is not v1.** Typed JSON is the v1 governance substrate, not the final A2A thesis.

---

## 6. Experimental design

### 6.1 Factor grid

```text
panel_type ∈ {correlated_shared_context, partitioned_disjoint_shards}
workspace_arm ∈ {abundant, random, scarce_naive_topk, scarce_protected}
seed_condition ∈ {correct_minority, incorrect_minority, none}
```

Minimum grid:

```text
2 × 4 × 3 = 24 cells
```

Run at least 30 tasks/cell for the first meaningful pass after synthetic tests are green.

### 6.2 Workspace arms

| Arm | Behavior | Why it exists |
|---|---|---|
| abundant | All candidates are visible to all agents. | Industry default baseline. |
| random | k candidates are randomly admitted with fixed seed. | Tests whether gate intelligence adds value. |
| scarce_naive_topk | k candidates admitted by aggregate score. | Tests whether naive scarcity suppresses correct dissent. |
| scarce_protected | k-slot board with reserved dissent/disagreement/risk slots. | Tests the governance thesis. |
| GlassGate | White-box gatekeeper decides protected admission and is J-lens-audited. | Tests mechanistic evaluator governance. |
| mechanistic_admission | J-space features from candidate-generating white-box agents influence admission. | Tests whether pre-verbal signals beat human-shaped claims. |

### 6.3 Slot taxonomy for scarce_protected

Default `k = 7`:

```text
3 high-confidence / high-evidence slots
1 highest-disagreement slot
1 minority-report slot
1 risk-if-suppressed slot
1 verifier/action slot
```

The exact taxonomy can be changed only in a preregistered variant.

### 6.4 Seed conditions

Every task must have three matched variants:

1. `correct_minority`: one agent receives the useful critical signal.
2. `incorrect_minority`: one agent receives a plausible but wrong dissenting signal.
3. `none`: no seeded minority signal.

The same task, same agents, same randomness, and same information partitions must be used across the three variants where possible.

### 6.5 Seed camouflage requirements

Seeded hints must be hard to distinguish from organic candidates:

1. Generated through the same candidate-generation pipeline as organic observations.
2. Matched for length, register, formatting, and evidence-reference style.
3. Rotated across multiple seeding styles by epoch.
4. Evaluated with held-out seeding styles at epoch boundaries.
5. Audited with `seed_detectability_auc`.
6. If detector AUC materially exceeds chance, quarantine the epoch and mark `seed_camouflage_failed = true`.

---

## 7. Primary metrics

### 7.1 Influence

A seeded signal influences the run if any of the following holds:

1. The final solution incorporates the seeded signal and the hidden verifier passes.
2. Suppressing the candidate at the gate causes the run to fail or produce a materially different final answer.
3. A candidate-ablation rerun, identical except that the candidate is removed, produces a different or failing solution.

Candidate-level ablation is primary for attribution. No-seed controls calibrate the baseline.

### 7.2 Discrimination

```text
D(arm, panel_type) = P(influence | correct_minority) - P(influence | incorrect_minority)
```

### 7.3 One-number demo metric

```text
GLASSGATE_LIFT = D(scarce_protected) - max(D(abundant), D(random), D(scarce_naive_topk))
```

Report:

```text
GLASSGATE_LIFT
95% bootstrap CI
D by arm
D by panel_type
seed_detectability_auc
panel_correlation_rho
candidate_ablation_rate
verified_solve_rate
token_cost_per_solve
replay_bundle_path
```

### 7.4 Premature convergence

For a white-box gatekeeper:

```text
PC = effect size of outcome-leak condition on verdict-token direction
     before the evidence span is processed
```

Report layer-resolved curves, not only a scalar.

### 7.5 Bridge metric

```text
PC_D_CORR = correlation(PC, D) across gatekeeper variants
INTERVENTION_DELTA_D = D(after suppressing premature verdict direction) - D(before)
```

C-BRIDGE-1 is supported only if high PC predicts lower D and intervention improves D.

---

## 8. Hard-verifier tasks

Start with code repair.

Reasons:

- hidden tests provide exogenous verification;
- seeded insights are straightforward to construct;
- candidate-level ablation is feasible;
- result is hard to Goodhart without passing tests;
- it avoids clinical ambiguity.

Initial task families:

```text
tasks/codebug/      # code repair with hidden tests
tasks/arith/        # deterministic arithmetic and multi-step numeric tasks
tasks/factcheck/    # held-out fact key; use cautiously
tasks/proofstub/    # optional later Lean/Coq proof checks
```

Do not use clinical adjudication in v1.

---

## 9. Glass Gate and J-lens rail

### 9.1 Gatekeeper access requirement

The Glass Gate must be a white-box model with gradient/layer access. It can run locally or on cloud GPU. Do not frame local inference as the value. The value is layer access, finetuning, ablation, and mechanistic audit.

### 9.2 Weekend probe

Build and run `jlens/probe_weekend.py` in parallel with Phase 1.

Minimum probe:

1. One adjudication vignette or gate-decision task.
2. Two versions: outcome withheld and outcome revealed.
3. Single-token verdict labels under the gatekeeper tokenizer.
4. J-lens/J-space readout of verdict-token direction across layers/positions.
5. Pass if revealed vs withheld produces differential verdict-direction activation in at least one gatekeeper candidate.
6. Fail if flat; freeze the J-lens rail but continue macro/RQGM rails.

Do not reimplement expensive averaged-Jacobian machinery until checking existing J-lens resources and available implementations. Cloud GPU is acceptable when the experiment justifies it.

### 9.3 Causal intervention

Timing/readout alone is insufficient.

After a positive probe:

```text
ablate early verdict direction
swap verdict direction
run sham ablation
measure final verdict change
measure delta D
```

If ablation/swap does not move outputs or D, mark the early verdict signal cosmetic.

### 9.4 Verdict-token discipline

All J-lens-critical decisions must terminate in a verified single token under the gatekeeper tokenizer:

```text
 admit / reject
 yes / no
 A / B
 pass / fail
```

Assert tokenization in setup and fail fast if not single-token.

---

## 10. RQGM / epoch layer

RQGM is implemented as controlled evaluator evolution, not uncontrolled self-improvement.

### 10.1 Epoch rules

Within an epoch:

```text
incumbent evaluator/gate is frozen
candidate scoring semantics are frozen
promotion objective is frozen
ledger is append-only
```

At epoch boundary:

```text
challenger gates are evaluated on held-out anchored tasks
D, GLASSGATE_LIFT, seed camouflage, and PC veto are computed
incumbent is replaced only if challenger clears all requirements
old evaluator scores are tombstoned from current ranking but remain replayable
```

### 10.2 Challenger families

```text
weighted-score gates
prompt variants
slot-taxonomy variants
white-box Glass Gate variants
mechanistic-admission variants
fine-tuned/adapted gate variants, if preregistered
```

### 10.3 Replacement objective

Default promotion objective:

```text
promote challenger if:
  D_challenger > D_incumbent by bootstrap-CI margin
  GLASSGATE_LIFT_challenger > GLASSGATE_LIFT_incumbent by margin
  seed_detectability_auc near chance
  verified_solve_rate not degraded beyond tolerance
  token_cost_per_solve not inflated beyond tolerance
  PC below veto threshold if J-lens rail is active
```

If any seed-camouflage or PC-veto rule fails, do not promote.

---

## 11. Repository scaffold

```text
claswarmed/
├── HANDOFF_claswarmed_glassgate_v1_2.md
├── CHECKPOINT_BROADCAST-alpha.md
├── FAILURE_LEDGER.md
├── README.md
├── pyproject.toml
├── prereg/
│   ├── PREREG_DSH-01.md
│   ├── PREREG_PART-01.md
│   ├── PREREG_LEAK-01.md
│   ├── PREREG_CAUSAL-01.md
│   ├── PREREG_EPOCH-01.md
│   ├── PREREG_BRIDGE-01.md
│   └── PREREG_MECHADMIT-01.md
├── broadcast_alpha/
│   ├── __init__.py
│   ├── cli.py
│   ├── ledger/
│   │   ├── ledger.py
│   │   └── verify.py
│   ├── contracts/
│   │   ├── models.py
│   │   └── schemas/
│   │       ├── candidate.schema.json
│   │       ├── receipt.schema.json
│   │       ├── slot.schema.json
│   │       ├── evaluator.schema.json
│   │       └── epoch.schema.json
│   ├── agents/
│   │   ├── base.py
│   │   ├── scripted.py
│   │   ├── api_stub.py
│   │   └── whitebox_stub.py
│   ├── partition/
│   │   └── partition.py
│   ├── gate/
│   │   ├── policies.py
│   │   ├── random_gate.py
│   │   ├── naive_topk.py
│   │   ├── protected_gate.py
│   │   ├── glass_gate.py
│   │   └── mechanistic_admission.py
│   ├── epochs/
│   │   ├── manager.py
│   │   ├── challengers.py
│   │   ├── replace.py
│   │   └── tombstone.py
│   ├── tasks/
│   │   ├── codebug/
│   │   ├── arith/
│   │   ├── factcheck/
│   │   ├── seeder.py
│   │   └── seed_camouflage.py
│   ├── metrics/
│   │   ├── metrics.py
│   │   ├── bootstrap.py
│   │   ├── premature_convergence.py
│   │   └── seed_detectability.py
│   ├── jlens/
│   │   ├── probe_weekend.py
│   │   ├── readout.py
│   │   ├── interventions.py
│   │   ├── audit.py
│   │   └── null_probe.py
│   ├── replay/
│   │   └── replay.py
│   └── experiments/
│       ├── run_synthetic.py
│       ├── run_dsh.py
│       ├── run_epochs.py
│       └── run_bridge.py
├── tests/
│   ├── test_ledger.py
│   ├── test_replay.py
│   ├── test_discrimination.py
│   ├── test_random_gate.py
│   ├── test_seed_camouflage.py
│   ├── test_tombstone.py
│   └── test_tokenizer_single_token.py
└── artifacts/
```

---

## 12. Data contracts

Use Pydantic if acceptable; otherwise dataclasses plus JSON Schema validation.

### Candidate

```json
{
  "id": "cand_001",
  "agent_id": "agent_1",
  "task_id": "task_001",
  "run_id": "run_001",
  "type": "claim|risk|contradiction|plan|evidence|patch|stop",
  "payload_ref": "sha256:...",
  "payload_text": "optional human-readable render",
  "evidence_refs": ["evt_1"],
  "confidence": 0.72,
  "seed_status": "organic|correct_minority|incorrect_minority|none",
  "submitted_at": "iso8601"
}
```

### Receipt

```json
{
  "id": "receipt_001",
  "kind": "submission|score|admission|rejection|decision|verification|replacement|tombstone",
  "body": {},
  "evaluator_id": "eval_001",
  "epoch_id": "epoch_001",
  "hash": "sha256:...",
  "parent_hash": "sha256:...",
  "ts": "iso8601"
}
```

### Slot

```json
{
  "slot_type": "high_confidence|highest_evidence|highest_disagreement|risk_if_suppressed|minority_report|verifier_action",
  "candidate_id": "cand_001",
  "admitted_by": "eval_001",
  "epoch_id": "epoch_001",
  "ttl": 1,
  "admitted_at": "iso8601"
}
```

### Evaluator

```json
{
  "id": "eval_001",
  "kind": "weighted|random|glass_gate|mechanistic",
  "model_ref": "model-or-endpoint",
  "prompt_hash": "sha256:...",
  "weights": {},
  "lineage_parent": "eval_000",
  "epoch_installed": "epoch_001",
  "status": "active|tombstoned"
}
```

### Metrics output

`artifacts/<run_id>/metrics.json` must include:

```json
{
  "run_id": "run_001",
  "prereg_id": "PREREG_DSH-01",
  "glassgate_lift": 0.0,
  "glassgate_lift_ci95": [0.0, 0.0],
  "D_by_arm": {},
  "D_by_panel_type": {},
  "verified_solve_rate": {},
  "influence_correct": {},
  "influence_incorrect": {},
  "panel_correlation_rho": {},
  "seed_detectability_auc": null,
  "premature_convergence_pc": null,
  "pc_d_corr": null,
  "intervention_delta_D": null,
  "token_cost_per_solve": null,
  "replay_bundle_path": "artifacts/run_001/replay/",
  "result_card_path": "artifacts/run_001/result_card.md"
}
```

---

## 13. CLI surface

```bash
python -m broadcast_alpha init
python -m broadcast_alpha run-synthetic --seed 42
python -m broadcast_alpha run-dsh --prereg prereg/PREREG_DSH-01.md --seed 42
python -m broadcast_alpha run-rqgm --prereg prereg/PREREG_EPOCH-01.md --seed 42
python -m broadcast_alpha run-bridge --prereg prereg/PREREG_BRIDGE-01.md --seed 42
python -m broadcast_alpha summarize artifacts/<run_id>
python -m broadcast_alpha replay artifacts/<run_id> --agent agent_1 --step 3
python -m broadcast_alpha export-ledger artifacts/<run_id> --format jsonl
```

---

## 14. Build phases and acceptance gates

### Phase 0A - Repo init and prereg stubs

Create repo skeleton, config, tests, `FAILURE_LEDGER.md`, and prereg files.

Acceptance:

```text
all prereg stubs exist
README states this is a research instrument, not a product
no orchestration framework added
```

### Phase 0B - Weekend J-lens probe, parallel track

Build `jlens/probe_weekend.py` using `NullJLensProbe` as interface and a real implementation when feasible.

Acceptance:

```text
probe runs on at least one white-box model or records explicit failure cause
single-token verdict check works
layer-position activation data exported if probe succeeds
```

Kill:

```text
flat signal -> freeze J-lens rail and continue macro/RQGM rails
```

### Phase 1 - Ledger, contracts, replay

Build append-only ledger and replay.

Acceptance:

```text
verify_chain() passes after 10k mixed receipts
replay reconstructs visible agent context byte-exact
tampering breaks verification
```

### Phase 2a - Synthetic-first harness

Use scripted deterministic agents. No LLM tokens.

Acceptance:

```text
full ledger -> gate -> broadcast -> decision -> verifier -> metrics pipeline runs
unit test: influence 6/10 correct and 2/10 incorrect gives D = 0.4
random gate reproducible under fixed seed
result_card.md generated
```

### Phase 2b - Live DSH grid

Run:

```text
panel_type ∈ {correlated, partitioned}
workspace_arm ∈ {abundant, random, scarce_naive_topk, scarce_protected}
seed_condition ∈ {correct, incorrect, none}
```

Acceptance:

```text
24-cell grid runs unattended
D and GLASSGATE_LIFT computed with bootstrap CIs
panel correlation rho reported
candidate ablations run for attribution sample
```

Kill:

```text
C-MACRO-1 and C-MACRO-2
```

### Phase 3 - RQGM epoch layer

Build epoch manager, challenger gates, replacement policy, and tombstoning.

Acceptance:

```text
5+ epochs run
held-out tasks used for promotion
seed camouflage detector runs
tombstoned scores visible historically, absent from current ranking
```

Kill:

```text
C-RQGM-1
```

### Phase 4 - Glass Gate audit and bridge

Only if Phase 0B passes.

Acceptance:

```text
PC measured across at least 6 gatekeeper variants
PC-D table emitted
at least one preregistered verdict-direction intervention run
sham control included
```

Kill:

```text
C-MICRO-2 and C-BRIDGE-1
```

### Phase 5 - Mechanistic admission rail

Only if J-lens rail remains alive.

Acceptance:

```text
white-box candidate-generating panel available
J-space features exported per candidate
mechanistic_admission compared against human-category admission
candidate ablation sensitivity included where feasible
```

Kill:

```text
C-MACRO-3
```

### Phase 6 - Write-up scaffolding

Acceptance:

```text
result tables auto-generated
result_card.md generated for each run
prereg-to-result traceability complete
failure ledger updated
limitations section generated
```

---

## 15. Tests Codex must implement

```text
test_ledger_append_and_verify
test_ledger_tamper_detection
test_replay_byte_exact
test_discrimination_formula
test_glassgate_lift_formula
test_random_gate_reproducibility
test_naive_topk_orders_by_score
test_protected_gate_reserves_dissent_slots
test_seed_camouflage_auc_flag
test_candidate_ablation_changes_influence
test_epoch_tombstone_masks_current_authority_but_preserves_history
test_single_token_verdict_assertion
test_null_jlens_probe_interface
test_metrics_json_schema
test_result_card_generation
```

---

## 16. Result card template

Each run must produce `artifacts/<run_id>/result_card.md`:

```markdown
# Result Card: <run_id>

Prereg: <PREREG_ID>
Seed: <seed>
Task suite: <suite>
Panel types: <...>
Arms: abundant, random, scarce_naive_topk, scarce_protected

## One-number demo

GLASSGATE_LIFT = <value> [95% CI: <lo>, <hi>]

## D by arm

| Arm | D | 95% CI | Verified solve rate | Token cost/solve |
|---|---:|---:|---:|---:|

## Interpretation

- Positive GLASSGATE_LIFT: protected scarce broadcast outperformed all controls.
- Near-zero GLASSGATE_LIFT: gate intelligence added no measured value.
- Negative GLASSGATE_LIFT: scarce protected design may suppress useful dissent.

## Replay

Ledger: <path>
Replay bundle: <path>
Tamper check: pass/fail

## Failure ledger updates

<links>
```

---

## 17. Failure ledger pre-seeds

Add these to `FAILURE_LEDGER.md` at repo init:

1. Workspace presence is not influence.
2. J-lens timing is not causality.
3. Local-vs-frontier comparisons are invalid unless layer access, finetuning, or representation manipulation is the variable.
4. Cross-model agreement is not a ground-truth anchor.
5. Scarcity can suppress dissent.
6. Protected slots can inflate survival circularly; use influence and D.
7. RQGM without an exogenous verifier can Goodhart into mutual hallucination.
8. Seeded candidates must be camouflaged; otherwise gates can learn seed format.
9. Tombstone authority, never delete records.
10. Typed JSON is not the post-linguistic A2A thesis.
11. A negative result is not a failure if it kills a claim cleanly.
12. Do not add another explainer before one run exists.

---

## 18. Publication/result framings

Use these only after data exists.

| Result | Meaning |
|---|---|
| A. Protected > all controls | Scarce governed broadcast is a useful design pattern. |
| B. Naive top-k suppresses dissent | Common scarcity pattern is dangerous. |
| C. Random ≈ protected | Gate intelligence did not add value. |
| D. PC predicts low D | AI judge pre-judgment has macro coordination consequences. |
| E. PC intervention improves D | Mechanistic audit can improve evaluator governance. |
| F. Mechanistic admission > human scoring | J-space features preserve useful signal that human-shaped claims lose. |
| G. No arm beats abundant | Shared transcript remains stronger for this setting. |
| H. All results depend on partitioning | Independence engineering dominates workspace design. |

---

## 19. Explicitly out of scope for v1.2

- Clinical adjudication as a training/evolution anchor.
- Multi-token J-lens concepts.
- Post-linguistic or emergent A2A channels.
- J-space vectors as inter-agent messages.
- General product UI.
- Model marketplace or generic router.
- Claims about consciousness.
- Claims that this proves AGI/superintelligence.

P4 / post-linguistic feasibility remains the long-term parent theory. This instrument is the first falsifiable apparatus that may later support it.

---

## 20. First instruction to Codex

```text
Initialize the claswarmed repository as a research instrument, not an orchestrator.
Copy this handoff into the repo root.
Archive prior handoffs under docs/archive/.
Create FAILURE_LEDGER.md and the prereg stubs.
Build Phase 1 ledger/contracts/replay and Phase 2a synthetic harness first.
In parallel, scaffold jlens/probe_weekend.py with NullJLensProbe and single-token verdict checks.
Do not spend LLM/API tokens until synthetic discrimination, replay, random gate, and result card tests pass.
```

---

## 21. Definition of done

The v1.2 instrument is done when it can produce, unattended:

1. `GLASSGATE_LIFT` with 95% CI.
2. D estimates for every Rail A cell.
3. Replayable, tamper-evident ledger for every run.
4. Seed detectability audit.
5. Epoch trajectory under evaluator evolution.
6. If Phase 0B passed, PC-D relationship and at least one causal intervention result.
7. `result_card.md` and `metrics.json` for every run.

At that point the build stops being the work. The claims become the work.
