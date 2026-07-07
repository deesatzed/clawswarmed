import argparse
import json
from pathlib import Path

from .experiments import run_dsh, run_rqgm, run_synthetic
from .jlens import run_jlens_gate
from .ledger import Ledger
from .live_dsh import run_live_dsh, run_live_smoke
from .live_gate import run_live_gate
from .orchestrator import run_all
from .reporting import build_result_report
from .replay import replay_context


def _emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="broadcast_alpha")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Print initialization status")

    run = sub.add_parser("run-synthetic", help="Run the deterministic synthetic harness")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--artifact-root", default="artifacts")

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

    if args.command == "run-synthetic":
        result = run_synthetic(seed=args.seed, artifact_root=Path(args.artifact_root))
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
