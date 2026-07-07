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

- `source_artifacts/ledger_stress_seed_42/`
- `source_artifacts/synthetic_seed_42/`
- `source_artifacts/dsh_seed_42/`
- `source_artifacts/rqgm_seed_42/`
- `source_artifacts/jlens_gate_seed_42/`
- `source_artifacts/live_gate_seed_42/`
- `source_artifacts/live_smoke_seed_42/`
- `source_artifacts/live_dsh_seed_42/`
- `source_artifacts/live_sequence_seed_42/`
- `final_report/`

## Current Result

```text
run_status = complete_with_deferred_jlens
GLASSGATE_LIFT = 0.4
glassgate_lift_ci95 = [0.15, 0.55]
seed_detectability_auc = 0.5
seed_adversarial_auc = 0.5
ledger_stress_synthetic_receipt_count = 10000
ledger_stress_mixed_kind_count = 8
ledger_stress_tamper_detection_passed = true
epoch_count = 5
jlens_rail_status = frozen
live_model_rail_status = unavailable
adapter_call_performed = false
live_model_run_performed = false
live_smoke_run_status = blocked_no_live_execution
live_smoke_adapter_call_count = 0
live_smoke_hidden_verifier_pass_rate = 0.0
live_dsh_run_status = blocked_no_live_execution
live_dsh_prereg_id = PREREG_LIVE-01
live_dsh_adapter_call_count = 0
live_dsh_hidden_verifier_pass_count = 0
live_dsh_hidden_verifier_pass_rate = 0.0
live_sequence_status = blocked_before_smoke
live_sequence_adapter_call_count_total = 0
live_sequence_smoke_status = blocked_no_live_execution
live_sequence_pilot_status = not_requested
live_sequence_pilot_promoted = false
all_child_ledgers_verified = true
```

## Replay

```bash
python3 -m broadcast_alpha replay artifacts/run_all_seed_42 --agent agent_1 --step 3
```

Expected context:

```text
unattended bundle: final report ready, all child ledgers verified, J-lens rail frozen/deferred, live sequence blocked_before_smoke, live model run not performed
```

## Boundary

This bundle is unattended and replayable, but it is still deterministic and
synthetic. It does not claim a live model-backed panel run. The live-provider
gate is included so the bundle records whether the model rail was configured,
authorized, and executed instead of leaving that gap implicit. The checked-in
bundle also includes the 10,000-receipt ledger stress proof, one-call live
smoke rail, the live DSH pilot rail, and the preferred live-provider sequence,
but it does not pass credentials, `--authorize-api-spend`, or `--execute-live`.
These live rails are preregistered under `prereg/PREREG_LIVE-01.md`; blocked
and fake-transport runs do not produce a live `GLASSGATE_LIFT` claim.

For future provider-backed execution, use `run-live-sequence` first. Its
default checked-in artifact is `artifacts/live_sequence_seed_42/`, and it is
blocked before smoke unless credentials, model, `--authorize-api-spend`, and
`--execute-live` are explicitly supplied.
