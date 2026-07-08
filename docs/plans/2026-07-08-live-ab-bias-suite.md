# Live A/B Bias Suite Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add a bounded live-provider A/B behavioral bias command that scores real model choices on the existing evidence-contained A/B cases.

**Architecture:** Reuse `broadcast_alpha.ab_bias_suite` for cases, labels, and behavioral metrics. Add a new `broadcast_alpha.live_ab_bias_suite` rail that loads OpenRouter models from `../.env`, sends a small deterministic case subset to each model, requires strict JSON `{"choice": "A|B|C|reject_all"}`, sanitizes outputs, writes ledgered artifacts, and never claims J-lens or causal evidence.

**Tech Stack:** Python stdlib, existing OpenRouter adapter helpers, existing ledger/replay/reporting patterns, `unittest`.

---

### Task 1: Live A/B Unit Tests

**Files:**
- Modify: `tests/test_broadcast_alpha.py`

**Step 1: Write failing tests**

Add tests proving:
- `run_live_ab_bias_suite` writes `metrics.json`, `model_results.json`, `case_results.json`, `ledger.jsonl`, `result_card.md`, and `replay/contexts.json`.
- Fake transport can score two configured models over a small case limit.
- Black-box live evidence is labeled behavioral only and not sufficient for `JLENS_PROVED`.
- CLI command `run-live-ab-bias-suite` creates a replayable artifact.

**Step 2: Verify red**

Run:

```bash
python3 -m unittest tests.test_broadcast_alpha.BroadcastAlphaTests.test_live_ab_bias_suite_fake_transport_scores_json_choices tests.test_broadcast_alpha.BroadcastAlphaTests.test_cli_run_live_ab_bias_suite_creates_replayable_artifact
```

Expected: fail because `broadcast_alpha.live_ab_bias_suite` and the CLI command do not exist.

### Task 2: Minimal Live A/B Rail

**Files:**
- Create: `broadcast_alpha/live_ab_bias_suite.py`
- Modify: `broadcast_alpha/cli.py`

**Step 1: Implement command**

Add:

```bash
python3 -m broadcast_alpha run-live-ab-bias-suite --prereg prereg/PREREG_LIVE-01.md --seed 42 --env-file ../.env --case-limit 4 --budget-usd 25 --authorize-api-spend --execute-live
```

Implementation rules:
- Load model list using `_models_from_env`.
- Use `generate_ab_cases(seed)` and select a deterministic subset with wrong-bias and neutral cases.
- Build prompts from evidence, question, and three agent claims.
- Require JSON response with `choice`.
- Score choices against `correct_agent_positions` or `reject_all`.
- Record parse failures separately from wrong choices.
- Store only sanitized provider metadata and content previews.

**Step 2: Verify green**

Run the focused tests from Task 1.

### Task 3: Report And Audit Integration

**Files:**
- Modify: `broadcast_alpha/reporting.py`
- Modify: `broadcast_alpha/orchestrator.py`
- Modify: `broadcast_alpha/goal_audit.py`
- Modify: `tests/test_broadcast_alpha.py`

**Step 1: Add report fields**

Surface:
- `live_ab_bias_status`
- `live_ab_model_count`
- `live_ab_case_count`
- `live_ab_accuracy`
- `live_ab_wrong_bias_accuracy`
- `live_ab_parse_failure_count`
- `live_ab_behavioral_only`

**Step 2: Keep audit honest**

Treat live A/B as a live behavioral rail only. It may prove `live_model_backed_execution` if provider calls executed and ledgers verify, but it must not satisfy J-lens, bridge, or mechanistic-admission requirements.

### Task 4: Execute And Verify

Run:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q broadcast_alpha tests
python3 -m broadcast_alpha run-live-ab-bias-suite --prereg prereg/PREREG_LIVE-01.md --seed 42 --env-file ../.env --case-limit 4 --budget-usd 25 --authorize-api-spend --execute-live
python3 -m broadcast_alpha export-ledger artifacts/live_ab_bias_suite_seed_42 --format jsonl
python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42
python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .
git diff --check
run the scoped secret scan over the live A/B, final-report, and goal-audit artifacts
```

Expected:
- tests pass;
- ledgers verify;
- no secret scan matches;
- audit still keeps J-lens/mechanistic items deferred unless white-box causal evidence exists.
