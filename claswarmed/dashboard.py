import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .council import build_council_plan
from .evidence import build_inventory
from .planner import build_showpiece_plan
from .rqgm import EvaluatorSlot, consider_replacement


def dashboard_payload(workspace: Path) -> dict:
    slot = EvaluatorSlot(name="code-review", incumbent="claude-reviewer", score=0.72)
    decision = consider_replacement(slot, challenger="gemini-reviewer", challenger_score=0.80)
    return {
        "inventory": build_inventory(workspace),
        "plan": build_showpiece_plan("claswarmed"),
        "council": build_council_plan("Build claswarmed", workspace),
        "epoch": {
            "slot": slot.name,
            "incumbent": slot.incumbent,
            "active_evaluator": decision.active_evaluator,
            "replaced": decision.replaced,
            "rationale": decision.rationale,
        },
    }


def render_dashboard(workspace: Path) -> str:
    payload = dashboard_payload(workspace)
    inventory_rows = "\n".join(
        f"<tr><td>{html.escape(item['path'])}</td>"
        f"<td>{html.escape(item['role'])}</td>"
        f"<td>{'present' if item['present'] else 'missing'}</td></tr>"
        for item in payload["inventory"]["items"]
    )
    phase_items = "\n".join(
        f"<li><strong>{html.escape(phase['name'])}</strong>: {html.escape(phase['goal'])}</li>"
        for phase in payload["plan"]["phases"]
    )
    council_rows = "\n".join(
        f"<tr><td>{html.escape(panel['perspective'])}</td>"
        f"<td>{html.escape(panel['assigned_model'])}</td>"
        f"<td>{html.escape(panel['tool_policy'])}</td>"
        f"<td>{html.escape(panel['focus'])}</td></tr>"
        for panel in payload["council"]["panels"]
    )
    epoch = payload["epoch"]
    data = html.escape(json.dumps(payload, indent=2))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>claswarmed</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; color: #172026; background: #f7f8f5; }}
    header {{ background: #14332d; color: white; padding: 24px clamp(16px, 4vw, 56px); }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 24px clamp(16px, 4vw, 32px); }}
    section {{ margin: 0 0 28px; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; letter-spacing: 0; }}
    h2 {{ font-size: 20px; margin: 0 0 12px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border-bottom: 1px solid #d8ddd2; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #e7ece1; }}
    code, pre {{ background: #172026; color: #edf2e9; border-radius: 6px; }}
    pre {{ padding: 14px; overflow: auto; }}
    .epoch {{ background: white; border-left: 5px solid #b43d2a; padding: 14px; }}
  </style>
</head>
<body>
  <header>
    <h1>claswarmed</h1>
    <p>CAM_Codx showpiece: persistent multi-model orchestration with RQGM evaluator epochs.</p>
  </header>
  <main>
    <section>
      <h2>Source Evidence</h2>
      <table>
        <thead><tr><th>Path</th><th>Role</th><th>Status</th></tr></thead>
        <tbody>{inventory_rows}</tbody>
      </table>
    </section>
    <section>
      <h2>Build Plan</h2>
      <ol>{phase_items}</ol>
    </section>
    <section>
      <h2>Council Plan</h2>
      <table>
        <thead><tr><th>Perspective</th><th>Model</th><th>Tools</th><th>Focus</th></tr></thead>
        <tbody>{council_rows}</tbody>
      </table>
    </section>
    <section class="epoch">
      <h2>RQGM Epoch Demo</h2>
      <p>Slot <code>{html.escape(epoch['slot'])}</code> selected <code>{html.escape(epoch['active_evaluator'])}</code>.</p>
      <p>{html.escape(epoch['rationale'])}</p>
    </section>
    <section>
      <h2>Machine Payload</h2>
      <pre>{data}</pre>
    </section>
  </main>
</body>
</html>"""


def serve_dashboard(workspace: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in {"/", "/index.html"}:
                self.send_error(404)
                return
            body = render_dashboard(workspace).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"claswarmed dashboard: http://{host}:{port}")
    server.serve_forever()
