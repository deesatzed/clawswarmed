# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Propagate the existing macro DSH diagnostics into the consolidated report,
run-all bundle, and goal audit.

## Actual User Goal

Move `GOAL_GLASSGATE.md` closer to a finished showpiece instrument by ensuring
the top-level evidence surfaces include the full preregistered macro result:
verified solve rate, panel correlation rho, candidate ablation rate, and token
cost per solve, not only `GLASSGATE_LIFT` and D-by-arm.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `broadcast_alpha/reporting.py` | Copy macro diagnostic fields from `dsh_seed_42/metrics.json` into final report metrics/result card/claim matrix. | Could imply live token cost exists when deterministic token cost is n/a. |
| `broadcast_alpha/orchestrator.py` | Carry those report metrics into `run-all` metrics/result card. | Run-all could drift from report if fields are omitted. |
| `broadcast_alpha/goal_audit.py` | Add or strengthen a requirement proving macro diagnostics are present. | Audit could overclaim if it only checks key presence. |
| `tests/test_broadcast_alpha.py` | TDD coverage for report, run-all, and audit propagation. | Tests must verify exact diagnostic keys and expected values. |
| `docs/FINAL_REPORT.md`, `docs/RUN_ALL.md`, `docs/GOAL_AUDIT.md`, `README.md` | Document the macro diagnostics now surfaced at top level. | Docs could confuse deterministic token-cost `null` with missing data. |
| Generated report/run-all/audit artifacts | Regenerated evidence after propagation. | Ledger timestamp churn in generated artifacts. |
| Root `DECISIONS.md`, `PROGRESS.md` | Record decision/progress. | Root is not Git-backed. |

## Existing Patterns To Follow

- `build-report` already reads `dsh_seed_42/metrics.json` and emits a single
  consolidated artifact.
- `run-all` already copies selected report metrics into the bundle metrics.
- `audit-goal` uses conservative `proved`, `deferred_with_record`, and
  `incomplete` statuses.
- Deterministic macro runs record `token_cost_per_solve = null` because no
  LLM/API tokens are used.

## Assumptions

- The macro DSH artifact is the authoritative source for these diagnostics.
- `token_cost_per_solve = null` is valid evidence for deterministic/no-token
  runs when paired with current no-live execution fields.
- This pass should not rerun or change live provider behavior.

## Non-Goals For This Pass

- Do not run OpenRouter or any external API.
- Do not change macro task outcomes or recompute formulas.
- Do not claim the active goal complete.
- Do not reopen J-lens.
- Do not mutate protected source repos.

## Step-by-Step Plan

1. Write failing tests requiring final report, run-all, and audit to expose the
   macro diagnostics.
2. Extend `build_result_report` to propagate the diagnostic fields and claim.
3. Extend `run_all` to carry those fields.
4. Extend `audit_goal` with a `macro_diagnostics` proof item.
5. Regenerate final report, run-all, and goal audit artifacts.
6. Update docs and root truth files.
7. Run full verification, commit, and push.

## Acceptance Criteria

- Final report metrics include:
  - `verified_solve_rate`
  - `panel_correlation_rho`
  - `candidate_ablation_rate`
  - `token_cost_per_solve`
- Run-all metrics include the same fields.
- Goal audit has a proved `macro_diagnostics` requirement.
- Result cards/docs display the diagnostics without implying live token spend.
- The overall goal audit remains `not_complete` until live/model-backed
  execution exists.

## Verification Plan

- `python3 -m unittest tests/test_broadcast_alpha.py`
- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q broadcast_alpha tests`
- `python3 -m py_compile claswarmed/*.py`
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts`
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`
- `python3 -m broadcast_alpha summarize artifacts/final_report_seed_42`
- `python3 -m broadcast_alpha summarize artifacts/run_all_seed_42`
- `python3 -m broadcast_alpha summarize artifacts/goal_audit_seed_42`
- `python3 -m broadcast_alpha export-ledger artifacts/final_report_seed_42 --format jsonl`
- `python3 -m broadcast_alpha export-ledger artifacts/run_all_seed_42 --format jsonl`
- `python3 -m broadcast_alpha export-ledger artifacts/goal_audit_seed_42 --format jsonl`
- `git diff --check`
- secret scan for provider key patterns in code/docs/artifacts
- `git status --short --branch`

## Rollback Plan

Revert the macro-diagnostics propagation commit and regenerate report/run-all
and goal-audit artifacts from the previous code.

## Risks

| Risk | Mitigation |
|---|---|
| Treating `token_cost_per_solve = null` as missing | Tests assert the key exists and remains null for deterministic no-token macro evidence. |
| Report/run-all drift | Tests check both surfaces. |
| Audit overclaims full completion | Audit adds only macro diagnostics; live/model-backed execution remains incomplete. |

## Proceed / Block Decision

Proceed. This pass is local, deterministic, no-spend, and within the app repo
plus root truth docs.
