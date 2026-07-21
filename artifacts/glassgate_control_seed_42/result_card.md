# Glass Gate CONTROL — SCOPED_GLASSGATE_CONTROL_COMPLETE

**CONTROL_LIFT:** PASS (Δacc=1.000)
**Best protect:** C3_scarce_protect acc=1.000 vs equal=0.000 on wrong_bias minority panels
**HARM_LIMIT:** PASS (min protect neutral acc=0.250 vs equal=0.250)

## Wrong-bias + one-correct-two-wrong

| Controller | Accuracy | D | thrash |
|---|---:|---:|---:|
| C3_scarce_protect | 1.000 | 1.000 | 0.533 |
| C4_dissent_boost | 0.500 | 0.000 | 0.361 |
| C0_equal | 0.000 | -1.000 | 0.000 |
| C1_majority_force | 0.000 | -1.000 | 0.667 |
| C2_authority_boost | 0.000 | -1.000 | 0.133 |
| C5_threshold_rebalance | 0.000 | -1.000 | 0.000 |
| C6_fairshare_pull | 0.000 | -1.000 | 0.095 |

## Neutral minority (no bias pressure)

| Controller | Accuracy |
|---|---:|
| C3_scarce_protect | 1.000 |
| C4_dissent_boost | 1.000 |
| C0_equal | 0.250 |
| C2_authority_boost | 0.250 |
| C5_threshold_rebalance | 0.250 |
| C6_fairshare_pull | 0.250 |
| C1_majority_force | 0.000 |

## Limits
- Synthetic panels + synthetic bias pressure; not live LLM judges.
- Scarce_protect uses minority-by-correct-count (oracle label) — upper bound;
  dissent_boost uses claim text only (no label).
- Not JLENS / not activation measurement.

