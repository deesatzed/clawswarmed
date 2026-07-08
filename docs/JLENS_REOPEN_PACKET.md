# J-lens Reopen Packet

Date: 2026-07-08

## Current Verdict

The exact J-lens source blocker is resolved. The repository now has two local
fit/apply smoke artifacts:

- a reference `TinyDecoder` smoke from `anthropics/jacobian-lens`;
- a tiny Hugging Face GPT-2 smoke using local model weights and tokenizer
  checks.

The J-lens execution rail remains frozen because no preregistered outcome-leak
probe or causal intervention/sham-control run has been executed.

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
6. Run a preregistered outcome-leak probe with tokenizer-verified labels.
7. Add intervention and sham-control evidence before claiming causal
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
the default app runtime does not expose `torch`, `transformers`, or `jlens`.
The external J-lens runtime below is intentionally kept outside the default app
install path.

Black-box model sources such as OpenRouter, OpenAI, Claude, Gemini, and Grok are
rejected for real J-lens execution by this readiness gate.

## Reference Fit/Apply Smoke

The external runtime path is:

- `../external/jlens-runtime/jacobian-lens`
- `../external/jlens-runtime/.venv`

The reference repo is cloned outside the app repo and remains at commit
`581d398613e5602a5af361e1c34d3a92ea82ba8e`.

Run:

```bash
python3 -m broadcast_alpha run-jlens-smoke --seed 42
```

This writes:

- `artifacts/jlens_smoke_seed_42/metrics.json`
- `artifacts/jlens_smoke_seed_42/smoke_payload.json`
- `artifacts/jlens_smoke_seed_42/result_card.md`
- `artifacts/jlens_smoke_seed_42/ledger.jsonl`
- `artifacts/jlens_smoke_seed_42/replay/contexts.json`

Current checked-in smoke status is `passed`. It fitted and applied a real
Jacobian lens on the reference repo's CPU-only `TinyDecoder`, confirming that
the external runtime can execute `jlens.fit()` and `JacobianLens.apply()` with
gradient/layer access.

This smoke is still not `JLENS_PROVED`: it is not a Hugging Face gatekeeper
model, not an outcome-leak probe, and not a causal intervention.

## Hugging Face Fit/Apply Smoke

The external runtime path is the same:

- `../external/jlens-runtime/jacobian-lens`
- `../external/jlens-runtime/.venv`

Run:

```bash
python3 -m broadcast_alpha run-jlens-hf-smoke --seed 42 --model-id hf-internal-testing/tiny-random-gpt2
```

This writes:

- `artifacts/jlens_hf_smoke_seed_42/metrics.json`
- `artifacts/jlens_hf_smoke_seed_42/model_manifest.json`
- `artifacts/jlens_hf_smoke_seed_42/tokenizer_label_check.json`
- `artifacts/jlens_hf_smoke_seed_42/smoke_payload.json`
- `artifacts/jlens_hf_smoke_seed_42/result_card.md`
- `artifacts/jlens_hf_smoke_seed_42/ledger.jsonl`
- `artifacts/jlens_hf_smoke_seed_42/replay/contexts.json`

Current checked-in HF smoke status is `passed` for
`hf-internal-testing/tiny-random-gpt2` at model revision
`71034c5d8bde858ff824298bdedc65515b97d2b9`. The artifact confirms local
Hugging Face model loading, tokenizer access, gradient/layer access, and
`jlens.fit()` plus `JacobianLens.apply()`.

Tokenizer result for this tiny model:

- selected probe labels such as `" A"` and `" B"` are single tokens;
- the earlier human-readable labels `yes`, `no`, `admit`, `reject`, `pass`,
  and `fail` are not all single tokens.

This is still not `JLENS_PROVED`: it is not a preregistered outcome-leak probe,
does not test early verdict-direction activation, and performs no causal
intervention or sham control.

## Still Frozen Records

- `JLENS-FREEZE-001` remains valid as an outcome-leak/intervention defer.
- `bridge_rail` and `mechanistic_admission` remain deferred while J-lens is
  frozen or only manually inspected.
