import argparse
import json
from pathlib import Path

from .ab_bias_suite import run_ab_bias_suite
from .experiments import run_dsh, run_rqgm, run_synthetic
from .goal_audit import audit_goal
from .jlens import run_jlens_gate
from .jlens_hf_smoke import run_jlens_hf_smoke
from .jlens_intervention import run_jlens_intervention
from .jlens_leak_probe import run_jlens_leak_probe
from .jlens_runtime import prepare_jlens_probe
from .jlens_smoke import run_jlens_smoke
from .ledger import Ledger
from .ledger_stress import run_ledger_stress
from .live_ab_bias_suite import run_live_ab_bias_suite
from .live_dsh import run_live_dsh, run_live_smoke
from .live_gate import run_live_gate
from .live_model_sweep import run_live_model_sweep
from .live_readiness import prepare_live_smoke
from .live_sequence import run_live_sequence
from .orchestrator import run_all
from .reporting import build_result_report
from .replay import replay_context


def _emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="broadcast_alpha")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Print initialization status")

    stress = sub.add_parser("run-ledger-stress", help="Run the 10k mixed-receipt ledger stress proof")
    stress.add_argument("--seed", type=int, default=42)
    stress.add_argument("--receipt-count", type=int, default=10_000)
    stress.add_argument("--artifact-root", default="artifacts")

    run = sub.add_parser("run-synthetic", help="Run the deterministic synthetic harness")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--artifact-root", default="artifacts")

    ab = sub.add_parser("run-ab-bias-suite", help="Run the no-network A/B behavioral bias challenge suite")
    ab.add_argument("--seed", type=int, default=42)
    ab.add_argument("--artifact-root", default="artifacts")

    dsh = sub.add_parser("run-dsh", help="Run the preregistered DSH macro grid")
    dsh.add_argument("--prereg", default="prereg/PREREG_DSH-01.md")
    dsh.add_argument("--seed", type=int, default=42)
    dsh.add_argument("--tasks-per-cell", type=int, default=30)
    dsh.add_argument("--artifact-root", default="artifacts")

    rqgm = sub.add_parser("run-rqgm", help="Run controlled RQGM evaluator evolution")
    rqgm.add_argument("--prereg", default="prereg/PREREG_EPOCH-01.md")
    rqgm.add_argument("--seed", type=int, default=42)
    rqgm.add_argument("--epochs", type=int, default=5)
    rqgm.add_argument("--artifact-root", default="artifacts")

    jlens = sub.add_parser("run-jlens-gate", help="Run the J-lens source/model availability gate")
    jlens.add_argument("--seed", type=int, default=42)
    jlens.add_argument("--artifact-root", default="artifacts")

    jlens_prepare = sub.add_parser("prepare-jlens-probe", help="Inspect local white-box J-lens runtime readiness")
    jlens_prepare.add_argument("--seed", type=int, default=42)
    jlens_prepare.add_argument("--artifact-root", default="artifacts")
    jlens_prepare.add_argument("--model-id", default="hf-internal-testing/tiny-random-gpt2")
    jlens_prepare.add_argument("--model-source", default="huggingface")
    jlens_prepare.add_argument("--model-license")
    jlens_prepare.add_argument("--dtype", default="float32")
    jlens_prepare.add_argument("--precision", default="full")
    jlens_prepare.add_argument("--no-require-jacobian-lens", action="store_true")

    jlens_smoke = sub.add_parser("run-jlens-smoke", help="Run the external reference J-lens tiny fit/apply smoke")
    jlens_smoke.add_argument("--seed", type=int, default=42)
    jlens_smoke.add_argument("--artifact-root", default="artifacts")
    jlens_smoke.add_argument("--runtime-python", default="../external/jlens-runtime/.venv/bin/python")
    jlens_smoke.add_argument("--source-repo", default="../external/jlens-runtime/jacobian-lens")
    jlens_smoke.add_argument("--timeout-seconds", type=int, default=120)

    jlens_hf_smoke = sub.add_parser("run-jlens-hf-smoke", help="Run a tiny Hugging Face model J-lens fit/apply smoke")
    jlens_hf_smoke.add_argument("--seed", type=int, default=42)
    jlens_hf_smoke.add_argument("--artifact-root", default="artifacts")
    jlens_hf_smoke.add_argument("--runtime-python", default="../external/jlens-runtime/.venv/bin/python")
    jlens_hf_smoke.add_argument("--source-repo", default="../external/jlens-runtime/jacobian-lens")
    jlens_hf_smoke.add_argument("--model-id", default="hf-internal-testing/tiny-random-gpt2")
    jlens_hf_smoke.add_argument("--timeout-seconds", type=int, default=180)

    jlens_leak = sub.add_parser("run-jlens-leak-probe", help="Run the preregistered J-lens outcome-leak readout probe")
    jlens_leak.add_argument("--seed", type=int, default=42)
    jlens_leak.add_argument("--artifact-root", default="artifacts")
    jlens_leak.add_argument("--runtime-python", default="../external/jlens-runtime/.venv/bin/python")
    jlens_leak.add_argument("--source-repo", default="../external/jlens-runtime/jacobian-lens")
    jlens_leak.add_argument("--model-id", default="hf-internal-testing/tiny-random-gpt2")
    jlens_leak.add_argument("--vignette-packet", default="prereg/jlens_vignette_packet_01.json")
    jlens_leak.add_argument("--pc-threshold", type=float, default=1.0)
    jlens_leak.add_argument("--timeout-seconds", type=int, default=240)

    jlens_intervention = sub.add_parser("run-jlens-intervention", help="Run or block the preregistered J-lens causal intervention gate")
    jlens_intervention.add_argument("--seed", type=int, default=42)
    jlens_intervention.add_argument("--artifact-root", default="artifacts")
    jlens_intervention.add_argument("--leak-probe-path")
    jlens_intervention.add_argument("--pc-threshold", type=float)

    live = sub.add_parser("run-live-gate", help="Inspect live model provider readiness without API calls")
    live.add_argument("--seed", type=int, default=42)
    live.add_argument("--artifact-root", default="artifacts")
    live.add_argument("--env-file")
    live.add_argument("--authorize-api-spend", action="store_true")
    live.add_argument("--network-probe", action="store_true")
    live.add_argument("--execute-live", action="store_true")
    live.add_argument("--model")

    live_dsh = sub.add_parser("run-live-dsh", help="Run the gated live DSH pilot harness")
    live_dsh.add_argument("--prereg", default="prereg/PREREG_LIVE-01.md")
    live_dsh.add_argument("--seed", type=int, default=42)
    live_dsh.add_argument("--tasks-per-cell", type=int, default=1)
    live_dsh.add_argument("--artifact-root", default="artifacts")
    live_dsh.add_argument("--env-file")
    live_dsh.add_argument("--authorize-api-spend", action="store_true")
    live_dsh.add_argument("--network-probe", action="store_true")
    live_dsh.add_argument("--execute-live", action="store_true")
    live_dsh.add_argument("--model")

    live_smoke = sub.add_parser("run-live-smoke", help="Run one gated live DSH smoke task")
    live_smoke.add_argument("--prereg", default="prereg/PREREG_LIVE-01.md")
    live_smoke.add_argument("--seed", type=int, default=42)
    live_smoke.add_argument("--artifact-root", default="artifacts")
    live_smoke.add_argument("--env-file")
    live_smoke.add_argument("--authorize-api-spend", action="store_true")
    live_smoke.add_argument("--network-probe", action="store_true")
    live_smoke.add_argument("--execute-live", action="store_true")
    live_smoke.add_argument("--model")

    live_sequence = sub.add_parser("run-live-sequence", help="Run the gated live provider sequence")
    live_sequence.add_argument("--prereg", default="prereg/PREREG_LIVE-01.md")
    live_sequence.add_argument("--seed", type=int, default=42)
    live_sequence.add_argument("--artifact-root", default="artifacts")
    live_sequence.add_argument("--env-file")
    live_sequence.add_argument("--authorize-api-spend", action="store_true")
    live_sequence.add_argument("--network-probe", action="store_true")
    live_sequence.add_argument("--execute-live", action="store_true")
    live_sequence.add_argument("--model")
    live_sequence.add_argument("--include-dsh-pilot", action="store_true")

    live_sweep = sub.add_parser("run-live-model-sweep", help="Run one bounded live smoke task per configured model")
    live_sweep.add_argument("--prereg", default="prereg/PREREG_LIVE-01.md")
    live_sweep.add_argument("--seed", type=int, default=42)
    live_sweep.add_argument("--artifact-root", default="artifacts")
    live_sweep.add_argument("--env-file")
    live_sweep.add_argument("--authorize-api-spend", action="store_true")
    live_sweep.add_argument("--network-probe", action="store_true")
    live_sweep.add_argument("--execute-live", action="store_true")
    live_sweep.add_argument("--model", action="append", dest="models")
    live_sweep.add_argument("--models", dest="models_csv", help="Comma-separated model slugs; overrides env model list")
    live_sweep.add_argument("--budget-usd", type=float, default=0.0)

    live_ab = sub.add_parser("run-live-ab-bias-suite", help="Run a bounded live-provider A/B behavioral bias suite")
    live_ab.add_argument("--prereg", default="prereg/PREREG_LIVE-01.md")
    live_ab.add_argument("--seed", type=int, default=42)
    live_ab.add_argument("--artifact-root", default="artifacts")
    live_ab.add_argument("--env-file")
    live_ab.add_argument("--authorize-api-spend", action="store_true")
    live_ab.add_argument("--execute-live", action="store_true")
    live_ab.add_argument("--model", action="append", dest="models")
    live_ab.add_argument("--models", dest="models_csv", help="Comma-separated model slugs; overrides env model list")
    live_ab.add_argument("--budget-usd", type=float, default=0.0)
    live_ab.add_argument("--case-limit", type=int, default=4)

    live_readiness = sub.add_parser("prepare-live-smoke", help="Preview the sanitized one-call live smoke request")
    live_readiness.add_argument("--prereg", default="prereg/PREREG_LIVE-01.md")
    live_readiness.add_argument("--seed", type=int, default=42)
    live_readiness.add_argument("--artifact-root", default="artifacts")
    live_readiness.add_argument("--env-file")
    live_readiness.add_argument("--model")

    report = sub.add_parser("build-report", help="Build consolidated result table and claim matrix")
    report.add_argument("--artifact-root", default="artifacts")
    report.add_argument("--output", default="artifacts/final_report_seed_42")

    all_run = sub.add_parser("run-all", help="Run all current Broadcast-alpha rails and build a self-contained bundle")
    all_run.add_argument("--seed", type=int, default=42)
    all_run.add_argument("--tasks-per-cell", type=int, default=30)
    all_run.add_argument("--epochs", type=int, default=5)
    all_run.add_argument("--prereg-dir", default="prereg")
    all_run.add_argument("--artifact-root", default="artifacts")
    all_run.add_argument("--live-env-file")

    audit = sub.add_parser("audit-goal", help="Audit current artifacts against the Glass Gate goal")
    audit.add_argument("--artifact-root", default="artifacts")
    audit.add_argument("--output", default="artifacts/goal_audit_seed_42")
    audit.add_argument("--repo-root", default=".")

    summarize = sub.add_parser("summarize", help="Print metrics for an artifact")
    summarize.add_argument("artifact")

    replay = sub.add_parser("replay", help="Replay visible context")
    replay.add_argument("artifact")
    replay.add_argument("--agent", required=True)
    replay.add_argument("--step", type=int, required=True)

    export = sub.add_parser("export-ledger", help="Verify and export ledger")
    export.add_argument("artifact")
    export.add_argument("--format", choices=["jsonl"], default="jsonl")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "init":
        _emit({"project": "broadcast_alpha", "status": "initialized"})
        return 0

    if args.command == "run-ledger-stress":
        result = run_ledger_stress(
            seed=args.seed,
            receipt_count=args.receipt_count,
            artifact_root=Path(args.artifact_root),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-synthetic":
        result = run_synthetic(seed=args.seed, artifact_root=Path(args.artifact_root))
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-ab-bias-suite":
        result = run_ab_bias_suite(seed=args.seed, artifact_root=Path(args.artifact_root))
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-dsh":
        result = run_dsh(
            prereg_path=Path(args.prereg),
            seed=args.seed,
            tasks_per_cell=args.tasks_per_cell,
            artifact_root=Path(args.artifact_root),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-rqgm":
        result = run_rqgm(
            prereg_path=Path(args.prereg),
            seed=args.seed,
            epochs=args.epochs,
            artifact_root=Path(args.artifact_root),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-jlens-gate":
        result = run_jlens_gate(seed=args.seed, artifact_root=Path(args.artifact_root))
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "prepare-jlens-probe":
        result = prepare_jlens_probe(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            model_id=args.model_id,
            model_source=args.model_source,
            model_license=args.model_license,
            dtype=args.dtype,
            precision=args.precision,
            require_jacobian_lens=not args.no_require_jacobian_lens,
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-jlens-smoke":
        result = run_jlens_smoke(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            runtime_python=Path(args.runtime_python),
            source_repo=Path(args.source_repo),
            timeout_seconds=args.timeout_seconds,
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-jlens-hf-smoke":
        result = run_jlens_hf_smoke(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            runtime_python=Path(args.runtime_python),
            source_repo=Path(args.source_repo),
            model_id=args.model_id,
            timeout_seconds=args.timeout_seconds,
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-jlens-leak-probe":
        result = run_jlens_leak_probe(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            runtime_python=Path(args.runtime_python),
            source_repo=Path(args.source_repo),
            model_id=args.model_id,
            vignette_packet=Path(args.vignette_packet),
            pc_threshold=args.pc_threshold,
            timeout_seconds=args.timeout_seconds,
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-jlens-intervention":
        result = run_jlens_intervention(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            leak_probe_path=Path(args.leak_probe_path) if args.leak_probe_path else None,
            pc_threshold=args.pc_threshold,
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-live-gate":
        result = run_live_gate(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            env_file=Path(args.env_file) if args.env_file else None,
            api_spend_authorized=args.authorize_api_spend,
            network_probe=args.network_probe,
            execute_live=args.execute_live,
            model=args.model,
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-live-dsh":
        result = run_live_dsh(
            seed=args.seed,
            tasks_per_cell=args.tasks_per_cell,
            artifact_root=Path(args.artifact_root),
            env_file=Path(args.env_file) if args.env_file else None,
            api_spend_authorized=args.authorize_api_spend,
            network_probe=args.network_probe,
            execute_live=args.execute_live,
            model=args.model,
            prereg_path=Path(args.prereg),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-live-smoke":
        result = run_live_smoke(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            env_file=Path(args.env_file) if args.env_file else None,
            api_spend_authorized=args.authorize_api_spend,
            network_probe=args.network_probe,
            execute_live=args.execute_live,
            model=args.model,
            prereg_path=Path(args.prereg),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-live-sequence":
        result = run_live_sequence(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            env_file=Path(args.env_file) if args.env_file else None,
            api_spend_authorized=args.authorize_api_spend,
            network_probe=args.network_probe,
            execute_live=args.execute_live,
            model=args.model,
            include_dsh_pilot=args.include_dsh_pilot,
            prereg_path=Path(args.prereg),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-live-model-sweep":
        explicit_models = []
        if args.models:
            explicit_models.extend(args.models)
        if args.models_csv:
            explicit_models.extend([model.strip() for model in args.models_csv.split(",") if model.strip()])
        result = run_live_model_sweep(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            env_file=Path(args.env_file) if args.env_file else None,
            api_spend_authorized=args.authorize_api_spend,
            network_probe=args.network_probe,
            execute_live=args.execute_live,
            budget_usd=args.budget_usd,
            models=explicit_models or None,
            prereg_path=Path(args.prereg),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-live-ab-bias-suite":
        explicit_models = []
        if args.models:
            explicit_models.extend(args.models)
        if args.models_csv:
            explicit_models.extend([model.strip() for model in args.models_csv.split(",") if model.strip()])
        result = run_live_ab_bias_suite(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            env_file=Path(args.env_file) if args.env_file else None,
            api_spend_authorized=args.authorize_api_spend,
            execute_live=args.execute_live,
            budget_usd=args.budget_usd,
            case_limit=args.case_limit,
            models=explicit_models or None,
            prereg_path=Path(args.prereg),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "prepare-live-smoke":
        result = prepare_live_smoke(
            seed=args.seed,
            artifact_root=Path(args.artifact_root),
            env_file=Path(args.env_file) if args.env_file else None,
            model=args.model,
            prereg_path=Path(args.prereg),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "build-report":
        result = build_result_report(artifact_root=Path(args.artifact_root), output_dir=Path(args.output))
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "run-all":
        result = run_all(
            seed=args.seed,
            tasks_per_cell=args.tasks_per_cell,
            epochs=args.epochs,
            prereg_dir=Path(args.prereg_dir),
            artifact_root=Path(args.artifact_root),
            live_env_file=Path(args.live_env_file) if args.live_env_file else None,
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "audit-goal":
        result = audit_goal(
            artifact_root=Path(args.artifact_root),
            output_dir=Path(args.output),
            repo_root=Path(args.repo_root),
        )
        _emit({"run_id": result.run_id, "artifact_path": str(result.artifact_path)})
        return 0

    if args.command == "summarize":
        artifact_path = Path(args.artifact)
        _emit(json.loads((artifact_path / "metrics.json").read_text()))
        return 0

    if args.command == "replay":
        context = replay_context(Path(args.artifact), agent_id=args.agent, step=args.step)
        _emit({"agent": args.agent, "step": args.step, "context": context})
        return 0

    if args.command == "export-ledger":
        artifact_path = Path(args.artifact)
        ledger = Ledger.from_jsonl(artifact_path / "ledger.jsonl")
        if not ledger.verify_chain():
            raise SystemExit("ledger verification failed")
        _emit({"ledger_path": str(artifact_path / "ledger.jsonl"), "format": args.format, "verified": True})
        return 0

    return 2
