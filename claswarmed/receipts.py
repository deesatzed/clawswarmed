import json
from datetime import datetime, timezone
from pathlib import Path
from time import time_ns


def save_run_receipt(app_root: Path, kind: str, payload: dict) -> dict:
    run_dir = app_root / ".claswarmed" / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = run_dir / f"{timestamp}-{time_ns()}-{kind}.json"
    manifest = {
        "kind": kind,
        "created_at": timestamp,
        "payload": payload,
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return {
        "kind": kind,
        "path": str(path),
        "created_at": timestamp,
    }
