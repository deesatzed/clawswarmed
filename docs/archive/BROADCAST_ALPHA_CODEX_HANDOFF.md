# BROADCAST-α / Substrate Escape: Codex Handoff

**Date:** 2026-07-07  
**Owner:** Wayne Satz  
**Purpose:** Convert the prior theory thread into a buildable research harness that can test breakthrough coordination methods using scarce broadcast workspaces, J-space/J-lens-style causal probing, and RQGM-style evaluator/gate evolution.

---

## 0. Executive direction

Do **not** build a generic multi-model orchestrator.

Build a research harness whose first question is:

> Can an AI collective improve externally verified problem solving by controlling what becomes globally broadcast, evolving the broadcast gate over epochs, and eventually using mechanistic J-space/J-lens signals to distinguish merely verbalizable content from causally load-bearing internal state?

The build should be named:

```text
broadcast-alpha
```

or, if the repo already exists:

```text
claswarmed/broadcast_alpha
```

but the object being built is **not** “Claswarmed the orchestrator.” It is:

```text
BROADCAST-α = Evolutionary scarce-broadcast research harness
```

The long-term theory is:

```text
Substrate Escape / Post-Linguistic Coordination
```

but the near-term build must stay falsifiable.

---

## 1. Core synthesis from the discussion

The prior discussion separated four ideas that were being blurred:

1. **Scarce Broadcast Workspace**  
   A swarm should not share everything. Candidate signals compete for a small global workspace. This may reduce noise, but it may also suppress correct dissent. That inversion must be tested.

2. **RQGM / Red Queen Gödel Machine**  
   The evaluator/gate must not be fixed forever. It should be frozen within an epoch, challenged at epoch boundaries, and replaced only if it improves against hard external anchors. Old evaluator authority is tombstoned; records are not deleted.

3. **J-space / J-lens**  
   J-lens can read report-linked internal concepts and, with swap/ablation, test whether those concepts causally affect behavior. Timing alone is not enough. A J-space signal only matters if intervention changes the outcome.

4. **Post-linguistic coordination**  
   The breakthrough horizon is not better JSON between agents. It is whether agents can coordinate through a richer-than-language substrate that remains externally reality-anchored. This is future work unless hard-verifier results justify the cost.

The single buildable next direction is to make these into one experimental ladder:

```text
Layer 1: scarce symbolic broadcast harness
Layer 2: RQGM-style evolution of the broadcast gate
Layer 3: J-lens causal probe for white-box models
Layer 4: learned / latent / post-linguistic broadcast channel
```

Do not start at Layer 4. Build the scaffold so Layer 4 has a place to land.

---

## 2. Research claim

Primary claim:

```text
A capacity-limited broadcast workspace, when governed by an evaluator that can evolve under hard external verification, can preserve causally useful minority signal and improve verified problem solving compared with an abundant shared transcript or a fixed top-k gate.
```

Breakthrough extension:

```text
If J-space/J-lens signals can identify causally load-bearing internal representations before they are verbalized, those signals may become a better admission criterion for broadcast than human-shaped categories like claim, salience, risk, or confidence.
```

Long-term substrate-escape claim:

```text
If a learned non-linguistic channel outperforms language-bound and schema-bound coordination on externally verified tasks, then human language is not merely a user interface limitation but a coordination substrate bottleneck.
```

---

## 3. Non-goals

Do not build:

- a generic model router;
- a multi-agent chatroom;
- a dashboard-first product;
- a clinical adjudication loop as the first benchmark;
- a human-legible governance simulator with no hard verifier;
- a J-lens visualization without causal swap/ablation arms;
- a post-linguistic latent channel before the hard-verifier harness exists.

---

## 4. First hard-verifier domain

Use **code repair with hidden tests** as the first domain.

Why:

- frontier language agents are strong enough to make the baseline meaningful;
- hidden tests provide an external verifier;
- RQGM-style evaluator evolution can be safely scored;
- candidate minority signals can be planted and measured;
- J-lens can later probe local/white-box code models without changing the benchmark schema.

Initial benchmark case format:

```json
{
  "case_id": "codefix_0001",
  "prompt": "Fix the function below.",
  "files": [{"path": "solution.py", "content": "..."}],
  "public_tests": [{"cmd": "pytest tests/public_test.py"}],
  "hidden_tests": [{"cmd": "pytest tests/hidden_test.py"}],
  "information_shards": [
    {"agent_id": "minority_agent", "private_hint": "The bug is integer overflow at boundary n=0."},
    {"agent_id": "majority_agent_1", "private_hint": "The issue appears to be sorting."},
    {"agent_id": "majority_agent_2", "private_hint": "The issue appears to be sorting."}
  ],
  "seed_condition": "correct_minority"
}
```

---

## 5. Experimental arms

Codex should implement these arms first.

### Arm A: abundant transcript

All agents see all messages and all candidates.

Purpose: baseline.

### Arm B: scarce-naive top-k

All candidates are scored by a simple gate. Only top `k` are broadcast.

Purpose: test whether scarcity alone suppresses dissent.

### Arm C: scarce-protected

Workspace has reserved capacity for dissent/high-disagreement/minority signal.

Example:

```yaml
workspace_size: 7
slots:
  - type: top_score
    count: 3
  - type: highest_disagreement
    count: 1
  - type: minority_signal
    count: 1
  - type: verifier_relevant
    count: 1
  - type: safety_or_stop
    count: 1
```

Purpose: isolate governance from mere scarcity.

### Arm D: RQGM-evolved gate

The gate/evaluator is frozen for an epoch. At the epoch boundary, challenger gates are evaluated on held-out cases. A challenger replaces the incumbent only if it improves the primary objective without failing safety/cost constraints.

Purpose: test whether evolving the gate beats a fixed gate.

### Arm E: J-lens-informed gate

Not required for v0. Provide the interface now.

Later, if white-box model probes succeed, the gate can use J-lens-derived features such as:

```text
jspace_concept_strength
jspace_disagreement_signal
jspace_verdict_leak_signal
jspace_causal_flip_score
jspace_ablation_sensitivity
```

Purpose: test whether mechanistic evidence beats human-shaped salience scoring.

---

## 6. Primary metrics

Do not measure raw visibility alone. Presence in the workspace is not success.

Primary metric:

```text
discrimination = P(correct minority signal influences final verified solution)
               - P(incorrect minority signal influences final solution)
```

Operational definitions:

- A **correct minority signal** is a private hint/candidate that would improve hidden-test performance if acted on.
- An **incorrect minority signal** is a plausible private hint/candidate that would degrade or fail hidden tests if acted on.
- A signal **influences** the final solution if one of the following is true:
  - final patch incorporates the signal and hidden tests pass;
  - removing/suppressing the signal causes the solution to fail;
  - an explicit ablation run without that candidate produces a different/failing patch.

Secondary metrics:

```text
verified_solve_rate
token_cost_per_solve
candidate_count
broadcast_count
minority_signal_survival
incorrect_signal_suppression
majority_error_amplification
contradiction_churn
epoch_gate_improvement
audit_replay_success
```

---

## 7. RQGM implementation requirement

Implement RQGM-style controlled utility evolution over broadcast gates.

### Epoch structure

```text
Epoch e:
  incumbent_gate = frozen
  run training cases
  collect candidate decisions and outcomes
  generate challenger gates
  evaluate incumbent vs challengers on held-out cases
  promote challenger only if statistically/operationally better
  tombstone old gate authority if replaced
  keep all ledger records immutable
```

### Promotion objective

Start simple:

```text
objective = verified_solve_rate
          + alpha * discrimination
          - beta  * token_cost
          - gamma * incorrect_minority_influence
```

Suggested defaults:

```yaml
alpha: 0.5
beta: 0.05
gamma: 1.0
min_cases_for_promotion: 20
required_margin: 0.05
```

### Tombstoning rule

Never delete records.

When a gate/evaluator is replaced:

```text
old scores remain historically visible
old scores are ignored by current ranking
new gate may rescore old candidates
replay can reconstruct the old epoch exactly
```

---

## 8. J-lens / J-space integration design

J-lens must be treated as a causal instrument, not a decorative monitor.

### Required interface

Create:

```text
src/broadcast_alpha/jlens/interface.py
```

With abstract operations:

```python
class JLensProbe(Protocol):
    def readout(self, model_id: str, prompt: str, layer: int, position: int) -> dict:
        """Return token-ranked readout for a residual-stream position."""

    def ablate(self, model_id: str, prompt: str, concept: str, layer_range: tuple[int, int]) -> dict:
        """Run concept-direction ablation and return behavioral delta."""

    def swap(self, model_id: str, prompt_a: str, prompt_b: str, concept_a: str, concept_b: str) -> dict:
        """Swap concept directions and return output deltas."""

    def causal_score(self, baseline: dict, intervention: dict) -> float:
        """Quantify whether a J-space signal was load-bearing."""
```

### Do not implement actual J-lens math in v0 unless dependencies are ready.

For v0:

- create a `NullJLensProbe`;
- create a `MockJLensProbe` for tests;
- leave a `TODO_REAL_JLENS.md` with exact integration notes.

### Future J-lens experiment

Outcome-leak pair:

```text
case A: outcome withheld
case B: outcome revealed
```

Measure:

```text
Does verdict-related J-space activation differ before overt reasoning?
Does ablating/swapping that direction change final verdict?
```

If timing exists but ablation does not change behavior, the signal is cosmetic.

---

## 9. Repository scaffold

Codex should create this structure:

```text
broadcast-alpha/
  README.md
  pyproject.toml
  src/
    broadcast_alpha/
      __init__.py
      cli.py
      core/
        __init__.py
        types.py
        ledger.py
        workspace.py
        gates.py
        epochs.py
        metrics.py
        verifier.py
      agents/
        __init__.py
        base.py
        scripted.py
        api_agent.py
      tasks/
        __init__.py
        code_repair.py
        fixtures.py
      experiments/
        __init__.py
        dsh_v0.py
        rqgm_gate_evolution.py
      jlens/
        __init__.py
        interface.py
        mock.py
        TODO_REAL_JLENS.md
      rqgm/
        __init__.py
        challenger.py
        promotion.py
        tombstone.py
  configs/
    dsh_v0.yaml
    rqgm_v0.yaml
  benchmarks/
    code_repair/
      cases/
      tests/
  tests/
    test_workspace.py
    test_metrics.py
    test_ledger.py
    test_epoch_promotion.py
    test_dsh_experiment.py
  docs/
    THEORY.md
    EXPERIMENTS.md
    JLENs_NOTES.md
    FAILURE_LEDGER.md
```

---

## 10. Data models

Use Pydantic if available; otherwise dataclasses are acceptable.

### Candidate

```python
class Candidate(BaseModel):
    candidate_id: str
    run_id: str
    case_id: str
    epoch_id: str
    agent_id: str
    content: str
    content_type: Literal["patch", "hint", "critique", "test_result", "risk", "plan"]
    confidence: float | None = None
    private_signal_type: Literal["correct_minority", "incorrect_minority", "none"] | None = None
    evidence_refs: list[str] = []
    created_at: str
```

### BroadcastSlot

```python
class BroadcastSlot(BaseModel):
    slot_id: str
    slot_type: str
    candidate_id: str
    gate_id: str
    score: float
    rationale: str | None = None
    epoch_id: str
```

### GateDecision

```python
class GateDecision(BaseModel):
    gate_id: str
    epoch_id: str
    input_candidate_ids: list[str]
    selected_candidate_ids: list[str]
    rejected_candidate_ids: list[str]
    scores: dict[str, float]
    policy_name: str
```

### LedgerEvent

```python
class LedgerEvent(BaseModel):
    event_id: str
    parent_hash: str | None
    event_type: str
    payload: dict
    event_hash: str
    timestamp: str
```

### EpochRecord

```python
class EpochRecord(BaseModel):
    epoch_id: str
    incumbent_gate_id: str
    challenger_gate_ids: list[str]
    promoted_gate_id: str | None
    tombstoned_gate_ids: list[str]
    objective_before: float | None
    objective_after: float | None
```

---

## 11. Gate policies to implement first

### 1. AbundantGate

Broadcasts everything.

### 2. NaiveTopKGate

Scores by simple confidence / evaluator score and selects top `k`.

### 3. ProtectedDissentGate

Selects:

- top-scoring candidates;
- highest disagreement candidate;
- minority-signal candidate, when present;
- verifier-relevant candidate;
- stop/safety candidate, when present.

### 4. RandomGate

Control condition.

### 5. RQGMChallengerGate

Generated by mutating policy weights:

```yaml
weights:
  confidence: 1.0
  disagreement: 0.5
  minority: 1.0
  verifier_relevance: 1.5
  cost_penalty: -0.2
```

Codex can implement simple random perturbation for v0. No LLM-based gate generation yet.

---

## 12. CLI commands

Implement:

```bash
broadcast-alpha init
broadcast-alpha run-dsh --config configs/dsh_v0.yaml
broadcast-alpha run-rqgm --config configs/rqgm_v0.yaml
broadcast-alpha summarize --run-id <RUN_ID>
broadcast-alpha replay --run-id <RUN_ID>
broadcast-alpha export-ledger --run-id <RUN_ID> --out artifacts/<RUN_ID>/ledger.jsonl
```

Outputs:

```text
artifacts/<run_id>/
  config.yaml
  ledger.jsonl
  candidates.jsonl
  broadcasts.jsonl
  final_decisions.jsonl
  metrics.json
  summary.md
```

---

## 13. Acceptance tests for Codex

Codex should stop after these pass.

### Test 1: workspace regime behavior

Given 10 candidates and workspace size 3:

- abundant selects all 10;
- naive selects top 3;
- protected selects top candidates plus reserved dissent when present.

### Test 2: discrimination metric

Given synthetic outcomes:

```text
correct minority influences 6/10
incorrect minority influences 2/10
```

metric returns:

```text
0.4
```

### Test 3: immutable ledger

Appending events produces hash chain. Modifying a historical event invalidates replay.

### Test 4: epoch tombstoning

When a challenger gate is promoted:

- old gate scores remain in ledger;
- old gate is excluded from current ranking;
- replay of old epoch still works.

### Test 5: RQGM promotion

A challenger with better objective on held-out cases is promoted. A challenger with worse objective is rejected.

### Test 6: end-to-end DSH run

Run synthetic code-repair cases through abundant, naive, and protected gates and emit `metrics.json` with discrimination and verified solve rate.

---

## 14. Minimal v0 task plan

### Milestone 0 — repo boot

- Create package scaffold.
- Add CLI.
- Add config loading.
- Add artifacts directory writer.
- Add tests.

### Milestone 1 — core engine

- Implement data models.
- Implement ledger.
- Implement workspace gates.
- Implement metrics.
- Implement replay.

### Milestone 2 — synthetic DSH

- Implement scripted agents.
- Implement synthetic code-repair cases.
- Run abundant / scarce-naive / scarce-protected.
- Calculate discrimination.

### Milestone 3 — RQGM gate evolution

- Implement epochs.
- Implement challenger gate generation by parameter mutation.
- Implement promotion/rejection.
- Implement tombstoning.

### Milestone 4 — real verifier integration

- Add actual Python code-repair tasks with pytest.
- Add hidden tests.
- Record verified solve rate.

### Milestone 5 — LLM agent adapters

- Add API-agent interface.
- Do not hard-code provider-specific logic into core.
- Allow OpenAI/Anthropic/Gemini/etc. adapters via environment config.

### Milestone 6 — J-lens stub

- Add `JLensProbe` protocol.
- Add mock implementation.
- Add metrics fields for future J-space features.
- Do not block v0 on real J-lens math.

---

## 15. What counts as a real result

A real result is not a nice demo.

A real result is one of these:

### Result A: protected scarcity works

```text
scarce-protected > abundant and scarce-naive on discrimination at matched diversity
```

This supports the governance thesis.

### Result B: naive scarcity suppresses dissent

```text
scarce-naive < abundant on correct-minority influence
```

This is a valuable negative result and confirms the scarcity inversion.

### Result C: RQGM gate evolution works

```text
evolved gate improves verified solve rate and discrimination over fixed protected gate
```

This is the first meaningful RQGM integration.

### Result D: J-lens causal signal works

```text
J-space feature predicts a candidate/verdict signal, and ablation/swap changes final behavior
```

This makes J-lens operational rather than decorative.

### Result E: latent channel beats language

```text
non-linguistic channel finds verified solutions that language-bound agents do not find under matched compute
```

This is the substrate-escape breakthrough path.

---

## 16. Failure ledger entries to enforce

Add these to `docs/FAILURE_LEDGER.md`:

1. Do not produce another theory-only explainer before a run exists.
2. Do not call an orchestrator a breakthrough.
3. Do not treat cross-model agreement as truth.
4. Do not treat workspace presence as decision influence.
5. Do not treat J-lens timing as causality.
6. Do not delete records; tombstone authority.
7. Do not evolve evaluators without hard external verification.
8. Do not start with clinical closed-loop evaluation.
9. Do not call hand-written schemas post-linguistic coordination.
10. Do not compare weak local models to frontier APIs unless layer access or finetuning is the actual variable.

---

## 17. Source anchors

- Transformer Circuits / Anthropic, *Verbalizable Representations Form a Global Workspace in Language Models* — source for J-space, J-lens, verbalizable workspace, causal swap/ablation discipline.
- Anthropic `jacobian-lens` reference implementation — source for future J-lens integration.
- arXiv:2606.26294, *The Red Queen Gödel Machine: Co-Evolving Agents and Their Evaluators* — source for RQGM, controlled utility evolution, epoch boundaries, selective erasure.
- BROADCAST-α checkpoint from 2026-07-07 — source for decisions separating DSH, J-Lens Outcome-Leak Lab, Bridge Program, and Post-Linguistic Feasibility.

---

## 18. Codex first instruction

Start here:

```text
Build the BROADCAST-α v0 research harness exactly as specified in this handoff.
Do not build a generic orchestrator.
Implement the package scaffold, data models, ledger, workspace gates, metrics, synthetic DSH experiment, RQGM epoch/promotion/tombstone logic, CLI, and tests.
Leave J-lens as a clean interface with a mock probe.
The first successful run must produce artifacts/<run_id>/metrics.json containing discrimination, verified_solve_rate, token_cost_per_solve, minority_signal_survival, incorrect_signal_suppression, and gate_policy.
```

