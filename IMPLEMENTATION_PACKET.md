# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add a bounded live model sweep command for the existing OpenRouter live smoke rail.

## Actual User Goal

Use the newly configured `.env` with seven OpenRouter models and a $25 key budget to test real model-backed execution without leaking secrets or overwriting one-model artifacts.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `tests/test_broadcast_alpha.py` | Add tests for numbered model parsing, fake sweep execution, CLI artifact creation, and goal audit recognition. | Low |
| `broadcast_alpha/live_model_sweep.py` | New sweep wrapper around `run_live_smoke`. | Medium |
| `broadcast_alpha/cli.py` | Add `run-live-model-sweep` command. | Low |
| `broadcast_alpha/goal_audit.py` | Treat a verified live model sweep as evidence for live model-backed execution. | Low |
| `docs/LIVE_DSH_PILOT.md`, `docs/LIVE_MODEL_GATE.md`, `README.md` | Document the seven-model workflow. | Low |
| `DECISIONS.md`, `PROGRESS.md` | Record the workflow decision and progress. | Low |

## Existing Patterns To Follow

- Existing live rails use `LiveDshResult`-style dataclasses, `metrics.json`, `ledger.jsonl`, `result_card.md`, and replay contexts.
- Existing command handlers emit only `run_id` and `artifact_path`.
- Provider artifacts must record secret presence, never secret values.
- Live rails default to blocked/no-spend unless both `--authorize-api-spend` and `--execute-live` are present.

## Assumptions

- `OPENROUTER_MODEL_1`, `OPENROUTER_MODEL_2`, etc. are the intended model list.
- A one-call smoke per model is the correct first bounded use of the $25 key.
- The provider/key budget is managed by the user's OpenRouter key cap; this command records the declared cap but does not enforce provider billing.

## Non-Goals For This Pass

- No full 24-cell live DSH pilot across all seven models.
- No J-lens implementation.
- No provider-side account or billing API integration.
- No exposure of API key values in artifacts or logs.

## Step-by-Step Plan

1. Add failing tests for model-list parsing and sweep behavior.
2. Implement the smallest sweep module that calls `run_live_smoke` once per model.
3. Add CLI plumbing.
4. Extend goal audit to accept verified sweep evidence.
5. Update docs and truth files.
6. Run focused tests, full tests, compile checks, and one bounded live sweep if code verification passes.

## Acceptance Criteria

- `run-live-model-sweep` reads numbered `OPENROUTER_MODEL_N` variables from an env file.
- Each model gets its own child artifact without overwriting another model.
- No secret value appears in sweep metrics, ledger, result card, or child artifacts.
- A no-spend invocation blocks with zero adapter calls.
- A fake-transport test records one call per model.
- Goal audit can mark live model-backed execution as proved when a real sweep records live calls.

## Verification Plan

- `python3 -m unittest tests.test_broadcast_alpha.BroadcastAlphaTests.<new tests>`
- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- One bounded real command after tests pass: `run-live-model-sweep --budget-usd 25 --authorize-api-spend --execute-live`.

## Rollback Plan

Revert the new module, CLI command, tests, docs, and audit extension. Existing live rails are not altered in behavior.

## Risks

| Risk | Mitigation |
|---|---|
| Provider rejects one or more configured model slugs. | Record adapter errors per model and continue; do not call this a full pass. |
| Costs exceed expectation. | Limit this command to one smoke call per model and record the declared budget cap. |
| Artifacts leak API keys. | Reuse existing sanitization and add tests scanning artifacts for dummy secrets. |

## Proceed / Block Decision

Proceed. The user supplied the `.env` and budget, and the implementation is a bounded wrapper over existing live rails.
