# J-lens Reopen Packet

Date: 2026-07-08

## Current Verdict

The exact J-lens source blocker is resolved. The J-lens execution rail remains
frozen because no local white-box model runtime, fitted Jacobian lens, or causal
intervention control has been run in this repository.

## Verified Exact Sources

| Source | Role | License | Verification |
|---|---|---|---|
| `https://github.com/anthropics/jacobian-lens` | Reference implementation | Apache-2.0 | `main` commit `581d398613e5602a5af361e1c34d3a92ea82ba8e`, accessed 2026-07-08 |
| `https://transformer-circuits.pub/2026/workspace/index.html` | Primary paper | External page terms | Accessed 2026-07-08 |

## Manual Sanity Surface

`https://www.neuronpedia.org/jlens` may be used for a no-code sanity check with
`prereg/jlens_vignette_packet_01.json`. A manual observation can guide whether
to spend engineering time on the white-box probe, but it cannot satisfy the
formal Glass Gate claim.

## Next Runtime Gate

Before any real probe is claimed:

1. Select an open-weight Hugging Face decoder model.
2. Confirm PyTorch gradient and layer activation access.
3. Clone or install `anthropics/jacobian-lens` outside this repo.
4. Verify tokenizer labels for `pass`, `fail`, `yes`, `no`, `admit`, and
   `reject` using the selected model tokenizer.
5. Run the smallest fit/apply smoke and write reproducible artifacts.
6. Add intervention and sham-control evidence before claiming causal
   prejudgment.

## Runtime Readiness Command

Run:

```bash
python3 -m broadcast_alpha prepare-jlens-probe --seed 42 --model-id hf-internal-testing/tiny-random-gpt2 --model-source huggingface
```

This writes:

- `artifacts/jlens_runtime_readiness_seed_42/metrics.json`
- `artifacts/jlens_runtime_readiness_seed_42/model_manifest.json`
- `artifacts/jlens_runtime_readiness_seed_42/tokenizer_label_check.json`
- `artifacts/jlens_runtime_readiness_seed_42/result_card.md`
- `artifacts/jlens_runtime_readiness_seed_42/ledger.jsonl`
- `artifacts/jlens_runtime_readiness_seed_42/replay/contexts.json`

Current checked-in readiness status is `blocked_missing_dependencies` because
this app runtime does not currently expose `torch`, `transformers`, or `jlens`,
and the verdict labels have not been checked with the selected tokenizer.

Black-box model sources such as OpenRouter, OpenAI, Claude, Gemini, and Grok are
rejected for real J-lens execution by this readiness gate.

## Still Frozen Records

- `JLENS-FREEZE-001` remains valid as a runtime/model/intervention defer.
- `bridge_rail` and `mechanistic_admission` remain deferred while J-lens is
  frozen or only manually inspected.
