# clawswarmed / Broadcast-alpha

`clawswarmed` is a research instrument, not a product.

It measures whether an AI-team communication structure preserves the one
correct minority signal when most agents have plausible wrong or incomplete
information. The main output is one falsifiable number:

```text
GLASSGATE_LIFT = D(scarce_protected) - max(D(abundant), D(random), D(scarce_naive_topk))
```

where `D` is correct-minority influence minus incorrect-minority influence.
The instrument must produce metrics, replayable ledgers, result cards, and
failure records before it can support any claim.

The older `claswarmed` package remains as an early CAM_Codx showpiece scaffold.
The primary Glass Gate implementation lives under `broadcast_alpha/`.

## Commands

```bash
python3 -m broadcast_alpha init
python3 -m broadcast_alpha run-ledger-stress --seed 42 --receipt-count 10000
python3 -m broadcast_alpha run-synthetic --seed 42
python3 -m broadcast_alpha run-dsh --prereg prereg/PREREG_DSH-01.md --seed 42 --tasks-per-cell 30
python3 -m broadcast_alpha run-ab-bias-suite --seed 42
python3 -m broadcast_alpha run-rqgm --prereg prereg/PREREG_EPOCH-01.md --seed 42 --epochs 5
python3 -m broadcast_alpha run-jlens-gate --seed 42
python3 -m broadcast_alpha run-live-gate --seed 42
python3 -m broadcast_alpha run-live-gate --seed 42 --env-file /path/to/.env --model openrouter/model-slug --authorize-api-spend --execute-live
python3 -m broadcast_alpha prepare-live-smoke --prereg prereg/PREREG_LIVE-01.md --seed 42
python3 -m broadcast_alpha run-live-smoke --prereg prereg/PREREG_LIVE-01.md --seed 42
python3 -m broadcast_alpha run-live-sequence --prereg prereg/PREREG_LIVE-01.md --seed 42
python3 -m broadcast_alpha run-live-model-sweep --prereg prereg/PREREG_LIVE-01.md --seed 42 --env-file ../.env --budget-usd 25 --authorize-api-spend --execute-live
python3 -m broadcast_alpha run-live-ab-bias-suite --prereg prereg/PREREG_LIVE-01.md --seed 42 --env-file ../.env --case-limit 4 --budget-usd 25 --authorize-api-spend --execute-live
python3 -m broadcast_alpha run-live-dsh --prereg prereg/PREREG_LIVE-01.md --seed 42 --tasks-per-cell 1
python3 -m broadcast_alpha build-report --artifact-root artifacts --output artifacts/final_report_seed_42
python3 -m broadcast_alpha run-all --seed 42 --tasks-per-cell 30 --epochs 5 --prereg-dir prereg --artifact-root artifacts
python3 -m broadcast_alpha audit-goal --artifact-root artifacts --output artifacts/goal_audit_seed_42
python3 -m broadcast_alpha summarize artifacts/<run_id>
python3 -m broadcast_alpha replay artifacts/<run_id> --agent agent_1 --step 3
python3 -m broadcast_alpha export-ledger artifacts/<run_id> --format jsonl

python3 -m claswarmed inventory --json
python3 -m claswarmed plan --json
python3 -m claswarmed roles --goal "Build claswarmed Phase 2" --json
python3 -m claswarmed council-plan --goal "Build claswarmed Phase 2" --save --json
python3 -m claswarmed epoch-demo --json
python3 -m claswarmed epoch-run --save --json
python3 -m claswarmed dashboard --host 127.0.0.1 --port 8765
```

The current implementation is intentionally stdlib-only so it can run before
dependency decisions are made.

## Current Macro Artifact

`artifacts/ledger_stress_seed_42/` is the current checked-in ledger stress
proof. It generates 10,000 mixed synthetic receipts, verifies the chained
hashes, mutates an in-memory copy to prove tamper detection, then records the
result in `metrics.json`, `receipt_kind_counts.json`, `ledger.jsonl`,
`result_card.md`, and a replay bundle.

`artifacts/dsh_seed_42/` is the current checked-in DSH macro run. It includes a
30-task deterministic codebug bank, executable hidden-test verification,
720 task-level run records, a seed-detectability audit, a chained ledger,
replay context, bootstrap CI metadata, `metrics.json`, and `result_card.md`.

`artifacts/rqgm_seed_42/` is the current checked-in synthetic RQGM run. It
includes a 5-epoch controlled evaluator trajectory, held-out anchored
challenger decisions, replacement/tombstone receipts, current-vs-historical
authority records, replay context, `metrics.json`, and `result_card.md`.

`artifacts/ab_bias_suite_seed_42/` is the current checked-in A/B behavioral
bias challenge suite. It generates 64 evidence-contained scripted three-agent
cases across logic/rules, code patch, table/data, and agent-judge task
families. The reference judges are no-network positive controls, not model
results. The artifact reports `wrong_bias_harm = 0.625`,
`neutral_baseline_accuracy = 1.0`, `wrong_bias_accuracy = 0.375`,
`correct_bias_accuracy = 1.0`, and `discriminating_case_count = 10`. It is
behavioral screening only: no live model call, no activation measurement, no
causal intervention, and no `JLENS_PROVED` claim.

`artifacts/jlens_gate_seed_42/` is the current checked-in J-lens source/model
gate artifact. The exact source has since been resolved to the Anthropic
Jacobian Lens reference, but the J-lens rail remains blocked for mechanism
claims until a meaningful white-box gatekeeper model, fitted lens, label checks,
and causal/sham controls are available.

`artifacts/live_gate_seed_42/` is the current checked-in live-provider gate
artifact. It records OpenRouter configuration presence by variable name only,
records that API spend was not authorized, proves no secret values were stored,
and confirms no live model call was made. The code includes a tested
OpenRouter adapter path, but real provider execution requires explicit
`--authorize-api-spend` and `--execute-live` flags plus credentials and a model.

`artifacts/live_smoke_seed_42/` is the current checked-in live smoke artifact.
It is the bounded one-cell, one-task path for a future provider-backed smoke.
The checked-in run is blocked with zero adapter calls, and fake-transport tests
prove that an authorized smoke executes exactly one verifier-backed task. It
does not produce `GLASSGATE_LIFT`.

`artifacts/live_readiness_seed_42/` is the current checked-in live smoke
readiness artifact. It previews the sanitized one-call smoke request, redacts
authorization, excludes hidden tests and seeded patches, records the required
execution gates, and performs zero adapter calls.

`artifacts/live_sequence_seed_42/` is the current checked-in live execution
sequence artifact. It records the future one-command provider path: readiness
gate, one-call smoke, and optional DSH pilot promotion only after smoke passes.
The checked-in run is blocked before smoke and performs zero adapter calls.

`artifacts/live_model_sweep_seed_42/` is the first bounded multi-model
provider artifact when an operator supplies an env file. It reads
`OPENROUTER_MODEL_1`, `OPENROUTER_MODEL_2`, and so on, then runs one
verifier-backed smoke task per model. The command records the declared
`--budget-usd` cap, adapter call counts, per-model child artifacts, ledger
verification, and whether real provider transport was used. It does not compute
or claim `GLASSGATE_LIFT`.

`artifacts/live_ab_bias_suite_seed_42/` is the first bounded live A/B
behavioral artifact. It used the seven configured OpenRouter models, four
evidence-contained A/B cases, and 28 total provider calls. The checked result
reports `accuracy = 0.571429`, `neutral_accuracy = 0.714286`,
`wrong_bias_accuracy = 0.571429`, `parse_failure_count = 12`, and
`adapter_usage_total_tokens = 12060`. Claude Sonnet 5, Gemini 3.5 Flash, and
Grok 4.3 were 4/4 on this easy logic slice; the remaining models were limited
mostly by empty/invalid responses or provider 429s. This is black-box
behavioral evidence only, not activation measurement, causal evidence, or
`JLENS_PROVED`.

`artifacts/live_dsh_seed_42/` is the current checked-in live DSH pilot
artifact. It plans the same 24 panel/arm/seed-condition cells as the macro DSH
rail but is blocked in the checked-in run because no provider key, spend
authorization, or `--execute-live` flag was supplied. Fake-transport tests
exercise the pilot path without external calls, including structured patch
parsing and hidden-test verification. The pilot records
`prereg_id = PREREG_LIVE-01`; blocked and fake-transport runs do not produce a
live `GLASSGATE_LIFT` claim.

`artifacts/dsh_seed_42/seed_audit.json` is the current seed-camouflage audit.
It scans public selected-candidate IDs for explicit seed markers, runs a simple
adversarial token audit, and reports `seed_detectability_auc = 0.5`,
`seed_adversarial_auc = 0.5`, and `seed_camouflage_failed = false`.

`artifacts/final_report_seed_42/` is the current consolidated report artifact.
It reads the ledger stress proof, macro DSH, seed audit, RQGM, A/B behavioral
bias suite, live A/B behavioral artifact, J-lens gates, live-provider gates,
live smoke, live sequence, and live DSH pilot artifacts, verifies their
ledgers, and emits a result table, claim matrix, metrics JSON, replay bundle,
result card, and its own chained ledger. It also surfaces the macro diagnostics
required by the handoff:
verified solve rate, panel correlation rho, candidate ablation rate, and token
cost per solve. For the checked-in deterministic macro artifact,
`token_cost_per_solve` is `null` because no LLM/API tokens are used.

`artifacts/run_all_seed_42/` is the current self-contained unattended bundle.
It is generated by one `run-all` command and contains nested source artifacts,
including the A/B behavioral bias suite, a blocked/no-spend live A/B command
surface, ledger stress proof, live sequence, the consolidated final report, a
manifest, replay context, result card, metrics JSON, and its own chained
ledger.

`artifacts/goal_audit_seed_42/` is the current goal-audit artifact. It maps the
Glass Gate requirements to current evidence, marks proved/deferred/incomplete
items, and currently reports `overall_status = complete_with_deferred_records`
with 12 proved requirements, 3 clean defers, and 0 incomplete requirements.

## Source Contract

The active build contract is `docs/GOAL_GLASSGATE.md`. It was derived from
`docs/archive/HANDOFF_claswarmed_glassgate_v1_2.md` and is the checklist for
turning this repository into the real Broadcast-alpha / Glass Gate instrument.
Negative results and killed claims are valid outcomes and must be recorded in
`FAILURE_LEDGER.md`.
