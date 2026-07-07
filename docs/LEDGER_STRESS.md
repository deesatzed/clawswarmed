# Ledger Stress Proof

Date: 2026-07-07

## Purpose

`run-ledger-stress` turns the Glass Gate requirement for at least 10,000 mixed
synthetic receipts into a replayable artifact. It is a ledger integrity proof,
not an experiment result and not live/model-backed execution.

## Command

```bash
python3 -m broadcast_alpha run-ledger-stress --seed 42 --receipt-count 10000
```

## Current Artifact

```text
artifacts/ledger_stress_seed_42/
```

Files:

- `metrics.json`
- `receipt_kind_counts.json`
- `result_card.md`
- `ledger.jsonl`
- `replay/contexts.json`

## Current Result

```text
synthetic_receipt_count = 10000
total_receipt_count = 10001
mixed_kind_count = 8
pre_metrics_chain_verified = true
ledger_verified = true
tamper_detection_passed = true
```

## Replay

```bash
python3 -m broadcast_alpha replay artifacts/ledger_stress_seed_42 --agent agent_1 --step 3
```

Expected context includes:

```text
ledger stress: tamper check passed
```

## Boundary

This proof says the append-only ledger can carry the required stress volume and
detect receipt mutation. It does not say live agents ran, does not use
OpenRouter, and does not change the goal audit's live/model-backed execution
gap.
