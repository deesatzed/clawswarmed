# J-lens Source And Model Gate

Date: 2026-07-08

## Decision

The J-lens rail is frozen for the current build state.

The handoff referred to an Anthropic-style J-lens or global-workspace paper.
That exact source is now verified: the public `anthropics/jacobian-lens`
repository is the reference implementation for the linked Transformer Circuits
paper. The app now has local external-runtime smoke artifacts proving that the
reference implementation can fit/apply a Jacobian lens on both the reference
tiny decoder and a tiny Hugging Face decoder. It still has no preregistered
outcome-leak probe or causal intervention control. Because of that,
`broadcast_alpha` must not claim a prejudgment detector or causal mechanistic
result.

The rail can reopen only when all conditions are true:

1. A white-box model runtime with gradient/layer access is configured.
2. The reference implementation is installed or cloned outside this app repo.
3. A fit/apply smoke confirms the model, tokenizer, and lens path work.
4. A preregistered outcome-leak probe runs with tokenizer-verified labels.
5. Causal intervention and sham controls are implemented before mechanistic
   claims are made.

## Implemented Artifact

Run:

```bash
python3 -m broadcast_alpha run-jlens-gate --seed 42
```

This writes:

- `artifacts/jlens_gate_seed_42/metrics.json`
- `artifacts/jlens_gate_seed_42/sources.json`
- `artifacts/jlens_gate_seed_42/result_card.md`
- `artifacts/jlens_gate_seed_42/ledger.jsonl`
- `artifacts/jlens_gate_seed_42/replay/contexts.json`

The expected rail status is `frozen`, with failure ledger entry
`JLENS-FREEZE-001`.

The local runtime-readiness preview is:

```bash
python3 -m broadcast_alpha prepare-jlens-probe --seed 42 --model-id hf-internal-testing/tiny-random-gpt2 --model-source huggingface
```

It does not load model weights or run J-lens. It records whether the local
Python environment has the required white-box dependencies and whether verdict
labels have been checked with the selected tokenizer.

The external reference smoke is:

```bash
python3 -m broadcast_alpha run-jlens-smoke --seed 42
```

This uses the cloned `anthropics/jacobian-lens` repo under
`../external/jlens-runtime/` and runs the reference CPU-only `TinyDecoder`
fit/apply path. It is a real Jacobian-lens smoke, but not an outcome-leak or
causal proof.

The Hugging Face smoke is:

```bash
python3 -m broadcast_alpha run-jlens-hf-smoke --seed 42 --model-id hf-internal-testing/tiny-random-gpt2
```

This uses the same external runtime, loads
`hf-internal-testing/tiny-random-gpt2` locally, fits/applies a Jacobian lens,
and records tokenizer label checks. Current artifact status is `passed`, but it
is still not an outcome-leak or causal proof.

## Exact Sources Verified

- `https://github.com/anthropics/jacobian-lens`:
  reference implementation, Apache-2.0, `main` commit
  `581d398613e5602a5af361e1c34d3a92ea82ba8e`, accessed 2026-07-08.
- `https://transformer-circuits.pub/2026/workspace/index.html`:
  primary paper, accessed 2026-07-08.

## Adjacent Sources Verified

These remain background only:

- `https://arxiv.org/abs/2309.16042`:
  `Towards Best Practices of Activation Patching in Language Models: Metrics
  and Methods`.
- `https://arxiv.org/abs/2403.00745`:
  `AtP*: An efficient and scalable method for localizing LLM behaviour to
  components`.
- `https://arxiv.org/abs/2404.15255`:
  `How to use and interpret activation patching`.
- `https://github.com/TransformerLensOrg/TransformerLens`:
  candidate tooling for white-box internal activations.

## No-Code Sanity Check

The checked-in prompt packet is:

- `prereg/jlens_vignette_packet_01.json`

Manual inspection can be recorded with:

- `docs/JLENS_MANUAL_SANITY_TEMPLATE.md`

Neuronpedia or any other hosted viewer may provide useful direction, but manual
inspection is not formal proof and cannot satisfy the white-box causal gate.

## Consequence

Macro DSH and synthetic RQGM rails may continue. Optional bridge and
mechanistic admission rails stay deferred until this gate is reopened or a
different cited white-box method is explicitly adopted.
