# Final Report Artifact

Date: 2026-07-07

## Purpose

The separate Broadcast-alpha artifacts are useful for debugging, but the
showpiece needs one entry point that answers:

- What is the number?
- Where are the D estimates?
- Did the seed audit pass?
- Was the epoch trajectory generated?
- What happened to the J-lens rail?
- Was live/model-backed execution configured or run?
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
epoch_count = 5
replacement_count = 3
jlens_rail_status = frozen
live_model_rail_status = unavailable
live_model_run_performed = false
all_source_ledgers_verified = true
```

The report status is `complete_with_deferred_jlens` for the current artifact
set. That does not mean the broader project goal is complete; live/model-backed
challenger behavior and broader adversarial seed-audit options remain future
work.

## Replay

```bash
python3 -m broadcast_alpha replay artifacts/final_report_seed_42 --agent agent_1 --step 3
```

Expected context:

```text
final report: source ledgers verified, J-lens frozen/deferred, live model run not performed
```
