# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add a `run-live-sequence` rail that automates the safe live-provider order:
provider readiness gate, one-call live smoke, and optional live DSH pilot only
after smoke passes. Default execution must remain blocked/no-spend.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to a real replayable Glass Gate instrument by
making the provider-backed path operational rather than a collection of manual
commands. The sequence should be the single command to run once credentials,
model, spend authorization, and `--execute-live` are intentionally supplied.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `broadcast_alpha/live_sequence.py` | New sequence rail with manifest, metrics, replay, and ledger. | Could accidentally perform more adapter calls than intended. |
| `broadcast_alpha/cli.py` | Add `run-live-sequence` with explicit live gates and optional `--include-dsh-pilot`. | CLI could obscure spend implications. |
| `tests/test_broadcast_alpha.py` | Add TDD coverage for blocked default, fake smoke pass, optional pilot promotion, and CLI artifact creation. | Fake transport tests could be mistaken for live evidence. |
| `README.md`, `docs/LIVE_DSH_PILOT.md`, `docs/RUN_ALL.md` | Document sequence as the safe provider-backed path. | Docs could overclaim current checked-in evidence. |
| `artifacts/` | Add `artifacts/live_sequence_seed_42/` in blocked no-credential mode. | Generated ledger churn. |
| Root `DECISIONS.md`, `PROGRESS.md` | Record workflow decision and progress. | Root is not Git-backed. |

## Existing Patterns To Follow

- Rail functions return dataclasses with `run_id`, `artifact_path`, and
  `expected_replay`.
- Every rail writes `metrics.json`, `result_card.md`, `ledger.jsonl`, and
  `replay/contexts.json`.
- `run-live-gate`, `run-live-smoke`, and `run-live-dsh` already preserve
  no-secret artifacts and require explicit execution flags.
- `run-all` uses nested source artifacts and child-ledger verification.
- Tests use fake/local transports for network-protected behavior.

## Assumptions

- No real OpenRouter request is allowed in this pass.
- The live sequence should not call the live gate adapter; it should use the
  gate as a no-call readiness record, then spend only on smoke when explicitly
  authorized.
- The optional live DSH pilot is disabled by default and should run only if the
  smoke rail records a verifier-backed pass.
- A fake transport can prove sequencing without external API calls.

## Non-Goals For This Pass

- Do not run a live model-backed call.
- Do not call OpenRouter or any external API.
- Do not add non-stdlib dependencies.
- Do not compute `GLASSGATE_LIFT` from live sequence, smoke, or pilot outputs.
- Do not add the sequence to `run-all` unless it remains blocked/no-spend by
  default.
- Do not reopen the J-lens rail.

## Step-by-Step Plan

1. Write failing tests for default blocked sequence, fake smoke execution, pilot
   promotion gating, and CLI artifact creation.
2. Implement `broadcast_alpha.live_sequence.run_live_sequence`.
3. Add CLI `run-live-sequence`.
4. Document the sequence as the future live-provider run path.
5. Generate checked-in blocked no-credential sequence artifact.
6. Run full verification and commit/push.

## Acceptance Criteria

- Default `run-live-sequence` writes `artifacts/live_sequence_seed_42/`.
- Default sequence performs zero adapter calls and records
  `sequence_status = blocked_before_smoke`.
- Fake transport with explicit live gates runs exactly one smoke adapter call by
  default and does not run the full DSH pilot.
- With `include_dsh_pilot = true`, fake transport runs the live DSH pilot only
  after smoke has a hidden-verifier pass.
- Sequence metrics include child artifact paths, child ledger verification,
  adapter call totals, promotion decision, and no `GLASSGATE_LIFT`.
- Existing synthetic, macro, RQGM, J-lens, report, run-all, live smoke, and
  live DSH tests pass.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m py_compile claswarmed/*.py`
- `python3 -m broadcast_alpha run-live-sequence --seed 42 --artifact-root artifacts --prereg prereg/PREREG_LIVE-01.md`
- `python3 -m broadcast_alpha export-ledger artifacts/live_sequence_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/live_sequence_seed_42 --agent agent_1 --step 3`
- `git diff --check`
- secret scan for provider key patterns in code/docs/artifacts
- `git status --short --branch`

## Rollback Plan

Revert the live sequence commit and remove `artifacts/live_sequence_seed_42/`.

## Risks

| Risk | Mitigation |
|---|---|
| Accidental network or spend | Default path keeps `execute_live = false`; tests use fake transport; pilot promotion is opt-in. |
| Secret leakage into artifacts | Reuse existing env/status sanitizers and scan artifacts before commit. |
| Overclaiming live behavior | Metrics and docs state blocked/fake sequence outputs are not live macro evidence and do not produce `GLASSGATE_LIFT`. |
| Pilot runs after failed smoke | Gate pilot promotion on smoke hidden-verifier pass count. |

## Proceed / Block Decision

Proceed. The pass does not require credentials, external spend, protected repo
mutation, or production deployment.
