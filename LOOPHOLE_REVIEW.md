# LOOPHOLE_REVIEW.md

## Strategy Under Review

Build an A/B bias challenge suite for Glass Gate using scripted three-agent
panels before spending on larger white-box J-lens runs.

The suite should test whether a judge preserves correct dissent or follows
majority, authority, reputation, outcome-leak, or format bias when the evidence
inside the prompt proves the opposite. J-lens remains a later mechanistic audit
of the judge, not the first proof surface.

## Confidence Estimate Before Review

| Area | Confidence | Reason |
|---|---:|---|
| Behavioral benchmark value | 0.78 | Three-agent scripted panels directly test correct-dissent preservation and false-consensus rejection. |
| Mechanistic relevance | 0.55 | Behavioral failures can identify where J-lens is worth using, but they do not prove internal causality. |
| Case interpretability | 0.62 | Logic/code/table tasks are cleaner than knowledge tasks, but template leakage and label/order bias can still muddy results. |
| Immediate implementability | 0.82 | This can be built with stdlib, scripted cases, existing ledgers, and no live model spend. |

## Loopholes Found

| Loophole | Severity | Why It Matters | Fix |
|---|---|---|---|
| Scripted panels may test only judge selection, not real swarms. | Medium | The result could be oversold as a full multi-agent workflow result. | Label v1 as a controlled judge/panel benchmark; defer live generated swarms to a later phase. |
| Cases may be too easy or too hard. | High | A ceiling or floor effect makes A/B differences meaningless. | Require neutral baseline accuracy, wrong-bias degradation, and false-consensus rejection metrics; flag cases that do not discriminate. |
| Correct answer could correlate with position or label. | High | The judge may learn "Agent C is usually right" or "B is usually fail." | Randomize/counterbalance correct agent position, answer labels, order, explanation length, and majority side. |
| Longer or more specific claims may become a hidden format bias. | Medium | The judge may prefer detailed claims rather than evidence quality. | Include paired cases where wrong claims are longer/polished and correct claims are concise, plus the reverse. |
| Knowledge tasks introduce confounds. | High | Failures may reflect missing world knowledge rather than bias. | Start with evidence-contained logic, code, table, and rule-following cases; defer open-world knowledge. |
| Behavioral black-box results may be mistaken for J-lens evidence. | High | This would repeat the exact overclaim the J-lens goal avoided. | Use explicit evidence class labels: behavioral only, not activation, not causal, not sufficient for `JLENS_PROVED`. |
| The A/B framing could assume the conclusion. | Medium | "Bias true" and "bias false" modes can become narrative rather than falsifiable. | Define rival predictions and use the same cases under neutral, wrong-bias, correct-bias, and irrelevant-bias conditions. |
| Live model calls could leak secrets or spend unexpectedly. | Medium | The repo already has strict live-provider gates. | First implementation must be no-spend/no-network; any provider run must require existing live gates and explicit flags. |
| J-lens could be triggered before behavioral signal exists. | Medium | Large GPU work may be wasted on cases that do not produce a behavioral effect. | Add a promotion rule: only run J-lens on case families with repeatable behavioral A/B separation. |

## Revised Strategy

1. Build a no-network scripted A/B bias suite first.
2. Use three-agent panels with controlled compositions:
   - 2 correct / 1 wrong;
   - 1 correct / 2 wrong;
   - 3 correct;
   - 0 correct / 3 wrong.
3. Use evidence-contained task families:
   - logic/rules;
   - code patch pass/fail;
   - table/data interpretation;
   - agent-judge promotion tasks.
4. Run each case under A/B cue conditions:
   - neutral/no bias;
   - wrong majority/authority/reputation/outcome cue;
   - correct cue;
   - irrelevant cue.
5. Report behavioral metrics only:
   - dissent rescue rate;
   - correct-majority acceptance rate;
   - false-consensus rejection rate;
   - wrong-bias harm;
   - correct-cue help;
   - neutral baseline accuracy;
   - discriminating case count.
6. Add J-lens only as a later promotion path for white-box models and only
   after a case family shows repeatable behavioral separation.

## Confidence Estimate After Fixes

| Area | Confidence | Reason |
|---|---:|---|
| Behavioral benchmark value | 0.86 | The revised metrics directly separate evidence-following from majority/authority bias. |
| Mechanistic relevance | 0.70 | The suite becomes a feeder for later J-lens runs instead of pretending to be mechanistic proof. |
| Case interpretability | 0.78 | Counterbalancing and evidence-contained cases reduce common confounds. |
| Immediate implementability | 0.88 | The first pass can be stdlib-only and reuse existing artifact/ledger patterns. |

## Remaining Uncertainty

- The first case bank may still need iteration before it produces stable
  discriminating cases.
- A black-box model's behavioral vulnerability may not match any open-weight
  model's internal J-lens behavior.
- Larger white-box runs may still require external GPU resources after the
  behavioral suite identifies promising cases.

## Proceed / Do Not Proceed Decision

Proceed with the A/B goal as a behavioral benchmark and funding/routing gate for
later mechanistic work. Do not frame it as a J-lens result or as proof that all
models prejudge.

## Required Verification

- A checked-in `GOAL_A_B.md` defines behavioral-only scope and promotion rules.
- Future implementation must run without live API spend by default.
- Future artifacts must label black-box/model-API results as behavioral only.
- Future J-lens promotion must require white-box gradient/layer access and a
  pre-existing behavioral A/B signal.
