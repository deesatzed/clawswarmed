# Run All Bundle

Date: 2026-07-07

## Purpose

The Glass Gate contract asks for an unattended instrument, not a collection of
manual one-off commands. `run-all` is the current one-command entry point for
the deterministic/synthetic v1 evidence bundle.

## Command

```bash
python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts
```

## Current Artifact

```text
artifacts/run_all_seed_42/
```

Top-level files:

- `manifest.json`
- `metrics.json`
- `result_card.md`
- `ledger.jsonl`
- `replay/contexts.json`

Nested artifacts:

- `source_artifacts/synthetic_seed_42/`
- `source_artifacts/dsh_seed_42/`
- `source_artifacts/rqgm_seed_42/`
- `source_artifacts/jlens_gate_seed_42/`
- `source_artifacts/live_gate_seed_42/`
- `final_report/`

## Current Result

```text
run_status = complete_with_deferred_jlens
GLASSGATE_LIFT = 0.4
glassgate_lift_ci95 = [0.15, 0.55]
seed_detectability_auc = 0.5
seed_adversarial_auc = 0.5
epoch_count = 5
jlens_rail_status = frozen
live_model_rail_status = unavailable
adapter_call_performed = false
live_model_run_performed = false
all_child_ledgers_verified = true
```

## Replay

```bash
python3 -m broadcast_alpha replay artifacts/run_all_seed_42 --agent agent_1 --step 3
```

Expected context:

```text
unattended bundle: final report ready, all child ledgers verified, J-lens rail frozen/deferred, live model run not performed
```

## Boundary

This bundle is unattended and replayable, but it is still deterministic and
synthetic. It does not claim a live model-backed panel run. The live-provider
gate is included so the bundle records whether the model rail was configured,
authorized, and executed instead of leaving that gap implicit. The checked-in
bundle does not pass credentials, `--authorize-api-spend`, or `--execute-live`.
