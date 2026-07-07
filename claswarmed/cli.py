import argparse
import json
from pathlib import Path

from .dashboard import serve_dashboard
from .evidence import build_inventory
from .planner import build_showpiece_plan
from .rqgm import EvaluatorSlot, consider_replacement


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print(payload.get("title") or payload.get("project") or "claswarmed")
    for item in payload.get("items", []):
        marker = "ok" if item.get("present") else "missing"
        print(f"- {marker}: {item['path']} ({item['role']})")
    for phase in payload.get("phases", []):
        print(f"- {phase['name']}: {phase['goal']}")


def _epoch_demo() -> dict:
    slot = EvaluatorSlot(name="code-review", incumbent="claude-reviewer", score=0.72)
    decision = consider_replacement(
        slot,
        challenger="gemini-reviewer",
        challenger_score=0.80,
    )
    return {
        "project": "claswarmed",
        "demo": "rqgm_epoch_transition",
        "slot": slot.name,
        "incumbent": slot.incumbent,
        "challenger": "gemini-reviewer",
        "active_evaluator": decision.active_evaluator,
        "replaced": decision.replaced,
        "rationale": decision.rationale,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claswarmed")
    sub = parser.add_subparsers(dest="command", required=True)

    inventory = sub.add_parser("inventory", help="Print source-evidence inventory")
    inventory.add_argument("--json", action="store_true")

    plan = sub.add_parser("plan", help="Print initial showpiece build plan")
    plan.add_argument("--json", action="store_true")

    epoch = sub.add_parser("epoch-demo", help="Run a toy RQGM epoch transition")
    epoch.add_argument("--json", action="store_true")

    dashboard = sub.add_parser("dashboard", help="Serve the local dashboard")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8765)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace = _workspace_root()

    if args.command == "inventory":
        _emit(build_inventory(workspace), args.json)
        return 0

    if args.command == "plan":
        _emit(build_showpiece_plan("claswarmed"), args.json)
        return 0

    if args.command == "epoch-demo":
        _emit(_epoch_demo(), args.json)
        return 0

    if args.command == "dashboard":
        serve_dashboard(workspace, host=args.host, port=args.port)
        return 0

    return 2

