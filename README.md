# clawswarmed / Broadcast-alpha

`clawswarmed` is a research instrument, not a product.

It measures whether an AI-team communication structure preserves the one
correct minority signal when most agents have plausible wrong or incomplete
information. The main output is one falsifiable number:

```text
GLASSGATE_LIFT = D(scarce_protected) - max(D(abundant), D(random), D(scarce_naive_topk))
```

where `D` is correct-minority influence minus incorrect-minority influence.
The instrument must produce metrics, replayable ledgers, result cards, and
failure records before it can support any claim.

The older `claswarmed` package remains as an early CAM_Codx showpiece scaffold.
The primary Glass Gate implementation lives under `broadcast_alpha/`.

## Commands

```bash
python3 -m broadcast_alpha init
python3 -m broadcast_alpha run-synthetic --seed 42
python3 -m broadcast_alpha run-dsh --prereg prereg/PREREG_DSH-01.md --seed 42 --tasks-per-cell 30
python3 -m broadcast_alpha summarize artifacts/<run_id>
python3 -m broadcast_alpha replay artifacts/<run_id> --agent agent_1 --step 3
python3 -m broadcast_alpha export-ledger artifacts/<run_id> --format jsonl

python3 -m claswarmed inventory --json
python3 -m claswarmed plan --json
python3 -m claswarmed roles --goal "Build claswarmed Phase 2" --json
python3 -m claswarmed council-plan --goal "Build claswarmed Phase 2" --save --json
python3 -m claswarmed epoch-demo --json
python3 -m claswarmed epoch-run --save --json
python3 -m claswarmed dashboard --host 127.0.0.1 --port 8765
```

The current implementation is intentionally stdlib-only so it can run before
dependency decisions are made.

## Source Contract

Build from `docs/archive/HANDOFF_claswarmed_glassgate_v1_2.md`. Negative
results and killed claims are valid outcomes and must be recorded in
`FAILURE_LEDGER.md`.
