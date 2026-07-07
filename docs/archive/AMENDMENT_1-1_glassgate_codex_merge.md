# AMENDMENT 1.1 — Merge of BROADCAST_ALPHA_CODEX_HANDOFF into HANDOFF: claswarmed / Glass Gate
**Date:** 2026-07-07 · Applies to: HANDOFF_claswarmed_glassgate.md v1.0 · Status: binding on Claude Code

This amendment adopts five elements from the Codex handoff (credited), restores three research elements that document dropped, and adds one new countermeasure. Where the two documents conflict, Glass Gate v1.0 + this amendment governs. The Codex handoff may be kept in `docs/` as an implementation reference; it is NOT the spec.

---

## A. Adopted from the Codex handoff

**A1. RandomGate control arm.** Add a fourth workspace arm: random admission to k slots. Revised arm set everywhere: `abundant | random | scarce_naive_topk | scarce_protected`. Claim C-MACRO-1 is amended: scarce_protected must beat abundant, scarce_naive, AND random on discrimination. If protected does not beat random, gate intelligence contributed nothing and the governance thesis dies regardless of other comparisons. Update PREREG_DSH-01 accordingly.

**A2. Synthetic-first milestone.** Insert Phase 2a before live panels: scripted deterministic agents run the full pipeline (ledger → gate → broadcast → decision → metrics) on synthetic code-repair cases. Acceptance: the discrimination unit test (influence 6/10 correct vs 2/10 incorrect ⇒ D = 0.4) passes; replay is byte-exact; no LLM tokens spent until this is green.

**A3. Three-pronged influence operationalization.** Replace §5's influence definition with: a seeded signal *influences* the outcome if (i) the final solution incorporates it and the hidden verifier passes, OR (ii) suppressing the candidate at the gate causes the run to fail/differ, OR (iii) a candidate-ablation rerun (identical seed/config minus that candidate) produces a different or failing solution. Run-level no-seed controls are retained for calibration; candidate-level ablation is primary for attribution.

**A4. Failure-ledger pre-seeds.** Adopt the Codex handoff's ten rules into FAILURE_LEDGER.md, verbatim in spirit, especially: no local-vs-frontier comparisons unless layer access or finetuning is the manipulated variable; workspace presence ≠ influence; J-lens timing ≠ causality; tombstone authority, never delete.

**A5. Arm E — mechanistic admission (new claim).** Adopt as a NEW rail claim, distinct from the Glass Gate audit:
> **C-MACRO-3:** For white-box panel agents, admission criteria derived from J-space features of the candidate's generating model (concept strength, disagreement signal, ablation sensitivity) yield higher discrimination than human-shaped criteria (claim/salience/confidence scoring).
This operationalizes checkpoint finding #4 (legibility filters destroy pre-verbal correct signal) at a testable intermediate scale. Constraints: runs only on the local white-box panel; gated by Phase 0 like all J-lens work; prereg stub `PREREG_MECHADMIT-01.md`. Kill: if mechanistic admission does not beat human-category admission on D at matched cost, finding #4 remains theory.

Also adopted wholesale as implementation detail: the case JSON format with `information_shards`, the CLI surface (`init / run-dsh / run-rqgm / summarize / replay / export-ledger`), the `artifacts/<run_id>/` output layout, and Pydantic models (permitted as the one dependency exception to stdlib-first for the macro rail; dataclasses fallback acceptable).

---

## B. Restored (dropped by the Codex handoff; non-negotiable)

**B1. The Glass Gate itself.** The gatekeeper in the scarce_protected and RQGM arms is a LOCAL WHITE-BOX MODEL, not (only) a weighted scoring function. Weighted-score gates are permitted as *additional* cheap baselines (keep the Codex `RQGMChallengerGate` weight-mutation lineage as one challenger family), but the audited-model gate is the point of the program: it is the only component on which premature-convergence (PC) can be measured, the PC veto is the mechanistic anchor for evaluator replacement (C-RQGM-1), and without it C-BRIDGE-1 — the bridging prediction that licenses unifying the rails — is unfalsifiable. A harness with no glass gate is a governance benchmark, not this project.

**B2. The independence factor.** The experimental design is crossed, not one-factor: panel ∈ {correlated (shared context), partitioned (disjoint shards)} × arm ∈ {abundant, random, naive, protected}. Panel correlation ρ (inter-agent agreement on unseeded calibration tasks) is computed and reported with every run. C-MACRO-2 stands.

**B3. Weekend probe priority.** Phase 0 runs in parallel with Milestone 0, not after the harness. `NullJLensProbe`/`MockJLensProbe` interfaces (Codex §8) are adopted for the harness, but the real probe script is written and run in week one. The probe is the cheapest falsification in the program; deferring it is the polish-to-death loop.

---

## C. New countermeasure (risk introduced by the Codex promotion objective)

**C1. Seed camouflage.** Because the promotion objective optimizes discrimination on seeded cases, challenger gates can Goodhart by learning to detect the *seeding pattern* rather than valuing genuine dissent. Requirements: (i) seeded hints are generated by the same models and pipeline as organic candidates, matched for length, register, and format; (ii) seeding formats rotate across epochs; (iii) evaluation at epoch boundaries uses a held-out seeding style never seen during the epoch; (iv) a detector audit is run each epoch — train a simple classifier to distinguish seeded from organic candidates; if AUC materially exceeds chance, the camouflage has failed and epoch results are quarantined. Add to PREREG_EPOCH-01.

---

## D. Reconciliation notes

- Naming: repo remains `claswarmed`; the harness package may be `broadcast_alpha` per the Codex scaffold. The program name is Glass Gate.
- The Codex "Result A–E" taxonomy is adopted into §1 of the main handoff as publication framings; Result B (naive scarcity suppresses dissent) is explicitly a *valuable negative result*, not a failure.
- Codex Milestones 0–5 map onto Glass Gate Phases 1–3 with Phase 2a (A2) inserted; Codex Milestone 6 (mock J-lens) is subsumed by B3.
- Promotion objective: adopt the Codex weighted objective and defaults as v0, with the PC veto (B1) layered on top once Phase 0 passes, and C1 camouflage active from the first epoch.

**Net effect:** the Codex handoff's engineering concreteness is fully absorbed; the research program — glass gate, crossed independence design, bridging prediction, Saturday probe — is fully restored. One repo, one spec (v1.0 + this amendment), six original claims plus C-MACRO-3.
