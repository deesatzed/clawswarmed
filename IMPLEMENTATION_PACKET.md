# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Add a `run-ledger-stress` proof rail that generates and verifies at least
10,000 mixed synthetic receipts, proves tamper detection, and wires that
artifact into the report, run-all bundle, and goal audit.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to the finished research instrument by turning
the explicit "verify_chain passes after at least 10,000 mixed synthetic
receipts" requirement into durable run evidence, not only a unit test.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `broadcast_alpha/ledger_stress.py` | New stress rail with 10k mixed receipts, metrics, result card, replay, ledger export, and tamper check. | Large generated ledger could be slow or hard to inspect. |
| `broadcast_alpha/cli.py` | Add `run-ledger-stress` command. | CLI surface grows; command must be clearly non-provider/non-LLM. |
| `broadcast_alpha/reporting.py` | Add ledger-stress row, metrics, and claim matrix evidence. | Report could overclaim if the artifact is missing. |
| `broadcast_alpha/orchestrator.py` | Include ledger stress in `run-all` and child-ledger verification. | Run-all runtime increases slightly. |
| `broadcast_alpha/goal_audit.py` | Audit the 10k mixed-receipt proof explicitly. | Audit must not mark proof complete from weak evidence. |
| `tests/test_broadcast_alpha.py` | Add TDD coverage for API, CLI, run-all/report propagation, and audit proof. | Tests must exercise 10k, not a smaller fixture, for the requirement. |
| `docs/LEDGER_STRESS.md`, `README.md` | Document the proof command and artifact. | Docs could imply live/model-backed completion; avoid that. |
| `artifacts/ledger_stress_seed_42/`, regenerated report/run-all/audit artifacts | Generated proof artifacts. | Generated ledger churn. |
| Root `DECISIONS.md`, `PROGRESS.md` | Record the decision and progress update. | Root is not Git-backed. |

## Existing Patterns To Follow

- Rail functions return dataclasses with `run_id`, `artifact_path`, and
  `expected_replay`.
- Every rail writes `metrics.json`, `result_card.md`, `ledger.jsonl`, and
  `replay/contexts.json`.
- `build-report`, `run-all`, and `audit-goal` already consolidate child
  artifacts and should be extended rather than bypassed.
- The audit uses conservative statuses and should keep the overall goal
  incomplete until real live/model-backed execution exists.

## Assumptions

- This pass should not call OpenRouter, CAM, or any external API.
- The ledger stress proof should use the existing append-only ledger class.
- "Mixed receipts" means multiple receipt kinds across candidate, gate,
  board, decision, verifier, metric, and epoch-shaped events.
- The generated artifact may include 10,001 total receipts if the final receipt
  records stress metrics after the 10,000 synthetic receipts.

## Non-Goals For This Pass

- Do not run a live model-backed call.
- Do not claim the goal complete.
- Do not change live gate semantics.
- Do not reopen the J-lens rail.
- Do not add dependencies.
- Do not mutate protected source repos.

## Step-by-Step Plan

1. Write failing tests for the ledger-stress API, CLI, report/run-all
   propagation, and goal audit evidence.
2. Implement `broadcast_alpha.ledger_stress.run_ledger_stress`.
3. Add the CLI command.
4. Wire the artifact into report, run-all, and audit.
5. Generate the default `artifacts/ledger_stress_seed_42/` artifact and
   regenerate final report, run-all, and goal audit.
6. Update docs and root truth files.
7. Run verification, commit, and push.

## Acceptance Criteria

- `run-ledger-stress` writes `artifacts/ledger_stress_seed_42/`.
- The artifact contains at least 10,000 synthetic stress receipts across
  multiple receipt kinds.
- `verify_chain()` passes for the exported stress ledger.
- A tampered copy fails chain verification and the result is recorded.
- `build-report`, `run-all`, and `audit-goal` surface this proof.
- Existing tests pass and the goal audit still marks live/model-backed
  execution incomplete.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m py_compile claswarmed/*.py`
- `python3 -m broadcast_alpha run-ledger-stress --seed 42 --receipt-count 10000`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
- `python3 -m broadcast_alpha export-ledger artifacts/ledger_stress_seed_42 --format jsonl`
- `python3 -m broadcast_alpha replay artifacts/ledger_stress_seed_42 --agent agent_1 --step 3`
- `python3 -m broadcast_alpha summarize artifacts/goal_audit_seed_42`
- `git diff --check`
- secret scan for provider key patterns in code/docs/artifacts
- `git status --short --branch`

## Rollback Plan

Revert the ledger-stress commit and remove
`artifacts/ledger_stress_seed_42/`. Regenerate report/run-all/audit artifacts
from the previous command set if needed.

## Risks

| Risk | Mitigation |
|---|---|
| Stress artifact becomes too heavy | Keep the payload compact and deterministic; store counts in metrics for inspection. |
| Audit overclaims completion | Add only a dedicated ledger-stress proof item; keep live/model-backed execution incomplete. |
| Test runtime increases | Use 10,000 receipts but compact bodies and no sleeps/network. |
| Tamper check mutates committed evidence | Mutate an in-memory loaded copy only, never the exported ledger file. |

## Proceed / Block Decision

Proceed. This pass does not require credentials, API spend, protected repo
mutation, production deployment, or external network access.
