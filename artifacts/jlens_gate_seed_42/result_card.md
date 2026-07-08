# Result Card: jlens_gate_seed_42

Seed: 42
Run type: J-lens source/model gate

## Decision

J-lens rail frozen.

The exact named J-lens source is now verified, but this runtime has no
configured white-box gatekeeper model with gradient/layer access, no fitted
Jacobian lens, and no causal intervention controls. No real J-lens probe was
implemented or run.

## Gate checks

| Check | Result |
|---|---|
| Exact source found | True |
| White-box model available | False |
| Real probe runnable | False |
| Single-token labels verified | 6 labels |

## Outcome

Rail status: frozen
Failure ledger entry: JLENS-FREEZE-001

## Replay

Ledger: artifacts/jlens_gate_seed_42/ledger.jsonl
Replay bundle: artifacts/jlens_gate_seed_42/replay
Tamper check: pass

## Failure ledger updates

Record `JLENS-FREEZE-001` in `FAILURE_LEDGER.md`.
