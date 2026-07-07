# Final Report Artifact

Date: 2026-07-07

## Purpose

The separate Broadcast-alpha artifacts are useful for debugging, but the
showpiece needs one entry point that answers:

- What is the number?
- Where are the D estimates?
- Did the seed audit pass?
- Did the 10,000-receipt ledger stress proof pass?
- Was the epoch trajectory generated?
- What happened to the J-lens rail?
- Was live/model-backed execution configured or run?
- Is the preferred live-provider sequence blocked, smoke-ready, or promoted?
- Do the ledgers verify?

`build-report` creates that single surface.

## Command

```bash
python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42
```

## Current Artifact

```text
artifacts/final_report_seed_42/
```

Files:

- `metrics.json`
- `result_table.json`
- `result_table.md`
- `claim_matrix.json`
- `ledger_verification.json`
- `result_card.md`
- `ledger.jsonl`
- `replay/contexts.json`

## Current Result

```text
GLASSGATE_LIFT = 0.4
glassgate_lift_ci95 = [0.15, 0.55]
seed_detectability_auc = 0.5
seed_adversarial_auc = 0.5
seed_camouflage_failed = false
ledger_stress_synthetic_receipt_count = 10000
ledger_stress_mixed_kind_count = 8
ledger_stress_tamper_detection_passed = true
epoch_count = 5
replacement_count = 3
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
all_source_ledgers_verified = true
```

The report status is `complete_with_deferred_jlens` for the current artifact
set. That does not mean the broader project goal is complete; live/model-backed
challenger behavior remains future gated work.

## Replay

```bash
python3 -m broadcast_alpha replay artifacts/final_report_seed_42 --agent agent_1 --step 3
```

Expected context:

```text
final report: source ledgers verified, J-lens frozen/deferred, live sequence blocked_before_smoke, live model run not performed
```
