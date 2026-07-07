import argparse
import json
from pathlib import Path

from .experiments import run_synthetic
from .ledger import Ledger
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

