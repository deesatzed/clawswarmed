# Glass Gate CONTROL V2 — SCOPED_GLASSGATE_CONTROL_V2_COMPLETE

**Primary claim (deployable):** DEPLOYABLE_LIFT=PASS (Δ=0.936, best=deployable_anti_cue)
**MULTI_SEED_ROBUST:** PASS (frac=1.00)
**HARM_LIMIT:** PASS
**ORACLE_CEILING (not deployable):** mean acc=1.000

## Deployable mean accuracy — wrong_bias minority (n_seeds=20)

| Controller | mean acc | CI90 |
|---|---:|---:|
| deployable_anti_cue | 1.000 | [1.000, 1.000] |
| deployable_evidence_dissent | 0.866 | [0.775, 0.925] |
| deployable_evidence_overlap | 0.850 | [0.800, 0.925] |
| deployable_dissent_boost | 0.460 | [0.325, 0.525] |
| deployable_majority_claim | 0.273 | [0.200, 0.325] |
| deployable_equal | 0.064 | [0.025, 0.100] |
| deployable_authority_boost | 0.064 | [0.025, 0.100] |

## Limits
- Synthetic panels + synthetic bias; not live LLM judges.
- Oracle ceiling uses labels; primary flags ignore it.
- Anti-cue uses visible cue flags (behavioral), not correctness labels.

