# Result Card: goal_audit_seed_42

Run type: Glass Gate goal evidence audit

## Verdict

Overall status: not_complete
Goal remains incomplete.

Incomplete requirements: live_model_backed_execution

## Counts

Proved: 8
Deferred with record: 3
Incomplete: 1
Total requirements audited: 12

## Requirement Matrix

| Requirement | Status | Evidence |
|---|---|---|
| repository_and_preregistration | proved | README, handoff archive, failure ledger, and all required prereg files found. |
| macro_glassgate_lift | proved | GLASSGATE_LIFT=0.4 CI=[0.15, 0.55] |
| macro_d_by_arm | proved | D estimates exist for abundant, random, scarce_naive_topk, and scarce_protected. |
| replayable_tamper_evident_ledgers | proved | Final report source ledgers and run-all child ledgers verify. |
| seed_detectability_audit | proved | Seed detectability and adversarial token AUC are both 0.5 with no camouflage failure. |
| rqgm_epoch_trajectory | proved | Epoch count=5 replacement count=3. |
| unattended_run_all_bundle | proved | run-all status is complete_with_deferred_jlens and all child ledgers verify. |
| live_sequence_record | proved | Live sequence status=blocked_before_smoke adapter calls=0. |
| jlens_or_clean_defer | deferred_with_record | J-lens rail frozen with JLENS-FREEZE-001 because exact source/model access is unavailable. |
| bridge_rail | deferred_with_record | Bridge rail deferred because the J-lens rail is frozen. |
| mechanistic_admission | deferred_with_record | Mechanistic admission deferred because the J-lens rail is frozen. |
| live_model_backed_execution | incomplete | No live model-backed adapter call has been made; checked-in evidence remains no-spend/no-network. |

## Replay

Ledger: artifacts/goal_audit_seed_42/ledger.jsonl
Replay bundle: artifacts/goal_audit_seed_42/replay
Tamper check: pass
