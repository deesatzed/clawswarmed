# J-lens Source And Model Gate

Date: 2026-07-07

## Decision

The J-lens rail is frozen for the current build state.

The handoff referred to an Anthropic-style J-lens or global-workspace paper,
but the exact paper, repository, or implementation was not verified in the
current source lookup. The app also has no configured white-box gatekeeper
model with gradient/layer access. Because of that, `broadcast_alpha` must not
claim a real J-lens probe, prejudgment detector, or causal mechanistic result.

The rail can reopen only when both conditions are true:

1. The exact J-lens source is identified and cited.
2. A white-box model runtime with gradient/layer access is configured.

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

## Sources Verified

The exact named source was not found. Adjacent primary/tooling sources were
verified only as background:

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

These sources do not satisfy the exact J-lens source requirement by themselves.

## Consequence

Macro DSH and synthetic RQGM rails may continue. Optional bridge and
mechanistic admission rails stay deferred until this gate is reopened or a
different cited white-box method is explicitly adopted.
