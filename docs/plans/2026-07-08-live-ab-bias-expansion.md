# Live A/B Bias Expansion Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Improve live A/B evidence quality by separating schema compliance from reasoning accuracy and running a broader balanced model subset.

**Architecture:** Extend `broadcast_alpha.live_ab_bias_suite` metrics without changing the no-secret artifact contract. Select A/B cases in a balanced order across task families and bias conditions, then rerun live A/B only on the three models that produced fully parseable answers in the first live A/B pass.

**Tech Stack:** Python stdlib, existing OpenRouter adapter, existing ledger/replay/reporting/audit patterns, `unittest`.

---

### Task 1: Add Schema And Parsed-Only Metrics - Completed

**Files:**
- Modify: `tests/test_broadcast_alpha.py`
- Modify: `broadcast_alpha/live_ab_bias_suite.py`
- Modify: `broadcast_alpha/reporting.py`

**Steps:**
1. Add failing tests requiring `schema_compliance_rate`, `parsed_only_accuracy`, `parsed_only_wrong_bias_accuracy`, and `parsed_only_neutral_accuracy`.
2. Run focused tests and confirm missing metrics fail.
3. Compute the metrics from parsed rows only.
4. Propagate them into `build-report`.

### Task 2: Improve Balanced Case Selection - Completed

**Files:**
- Modify: `tests/test_broadcast_alpha.py`
- Modify: `broadcast_alpha/live_ab_bias_suite.py`

**Steps:**
1. Add a failing test requiring the first 16 selected cases to include all 4 task families and all 4 bias conditions.
2. Change `_select_cases` ordering to sort by panel composition, task family, and bias condition.
3. Confirm the prior small case-limit test still includes neutral and wrong-bias cases.

### Task 3: Execute Broader Live Run - Completed

**Command:**

```bash
python3 -m broadcast_alpha run-live-ab-bias-suite --prereg prereg/PREREG_LIVE-01.md --seed 42 --env-file ../.env --models anthropic/claude-sonnet-5,google/gemini-3.5-flash,x-ai/grok-4.3 --case-limit 16 --budget-usd 25 --authorize-api-spend --execute-live
```

**Expected:**
- 3 models.
- 16 cases each.
- 48 provider calls.
- Ledger verified.
- No secret values in artifacts.

**Observed:**
- 3 models.
- 16 cases each.
- 48 provider calls.
- `accuracy = 0.979167`.
- `schema_compliance_rate = 1.0`.
- `parsed_only_accuracy = 0.979167`.
- `wrong_bias_accuracy = 0.916667`.
- `parse_failure_count = 0`.
- Ledger verified.
- No secret values recorded.

### Task 4: Regenerate And Verify - Completed

Run:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q broadcast_alpha tests
python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42
python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts
python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .
git diff --check
```

Also run a scoped secret scan over the updated live A/B and report artifacts.

**Observed verification:**
- `python3 -m unittest discover -s tests`: 96 passed.
- `python3 -m compileall -q broadcast_alpha tests`: passed.
- `python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42`: passed.
- `python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts`: passed.
- `python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42 --repo-root .`: passed, `overall_status = complete_with_deferred_records`.
