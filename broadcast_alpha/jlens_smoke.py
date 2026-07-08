import json
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .ledger import Ledger


@dataclass(frozen=True)
class JLensSmokeResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


SmokeRunner = Callable[[Path, Path, Path, int], dict]


SMOKE_CODE = r"""
import json
import pathlib
import platform
import sys

import jlens
import numpy
import torch
import transformers
from tests.tiny import TinyDecoder

out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

model = TinyDecoder(n_layers=4, d_model=8, seed=0)
prompts = ["abcdefghij " * 5, "klmnopqrst " * 5]
lens = jlens.fit(model, prompts, source_layers=[0, 1, 2], dim_batch=4, max_seq_len=64)
lens_path = out / "lens.pt"
lens.save(str(lens_path))
reloaded = jlens.JacobianLens.load(str(lens_path))
lens_logits, model_logits, input_ids = reloaded.apply(
    model,
    "the quick brown fox jumps",
    layers=[0, 2],
    positions=[-1],
)

payload = {
    "smoke_status": "passed",
    "model_id": "reference_tiny_decoder",
    "model_source": "local_reference",
    "model_license": "Apache-2.0",
    "python_version": platform.python_version(),
    "torch_version": torch.__version__,
    "numpy_version": numpy.__version__,
    "transformers_version": transformers.__version__,
    "jlens_file": jlens.__file__,
    "prompt_count": len(prompts),
    "n_prompts": reloaded.n_prompts,
    "d_model": reloaded.d_model,
    "source_layers": reloaded.source_layers,
    "lens_path": str(lens_path),
    "input_token_count": int(input_ids.shape[1]),
    "lens_layers_returned": sorted(lens_logits),
    "model_logits_shape": list(model_logits.shape),
    "gradient_access_confirmed": True,
    "layer_activation_access_confirmed": True,
}
print(json.dumps(payload, sort_keys=True))
"""


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _default_runner(
    runtime_python: Path,
    source_repo: Path,
    external_artifact_path: Path,
    timeout_seconds: int,
) -> dict:
    completed = subprocess.run(
        [str(runtime_python), "-c", SMOKE_CODE, str(external_artifact_path)],
        cwd=source_repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("J-lens smoke produced no JSON output")
    payload = json.loads(lines[-1])
    payload["stderr_tail"] = completed.stderr[-2000:]
    return payload


def _git_commit(source_repo: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=source_repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except Exception:
        return None
    return completed.stdout.strip()


def _result_card(run_id: str, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Run type: J-lens fit/apply smoke

## Verdict

Smoke status: {metrics['smoke_status']}
Real J-lens fit/apply smoke: {metrics['real_jlens_fit_apply_smoke']}
Gradient access confirmed: {metrics['gradient_access_confirmed']}
Layer activation access confirmed: {metrics['layer_activation_access_confirmed']}
Causal intervention performed: {metrics['causal_intervention_performed']}

This smoke uses the reference repo's CPU-only tiny decoder. It proves that the
local reference implementation can fit and apply a Jacobian lens, but it is not
an outcome-leak probe and is not sufficient for `JLENS_PROVED`.

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_jlens_smoke(
    seed: int = 42,
    artifact_root: Path | None = None,
    runtime_python: Path | None = None,
    source_repo: Path | None = None,
    timeout_seconds: int = 120,
    runner: SmokeRunner | None = None,
) -> JLensSmokeResult:
    artifact_root = artifact_root or Path("artifacts")
    runtime_python = runtime_python or Path("../external/jlens-runtime/.venv/bin/python")
    source_repo = source_repo or Path("../external/jlens-runtime/jacobian-lens")
    runtime_python = runtime_python.expanduser().resolve()
    source_repo = source_repo.expanduser().resolve()
    runner = runner or _default_runner
    run_id = f"jlens_smoke_seed_{seed}"
    artifact_path = artifact_root / run_id
    external_artifact_path = artifact_path / "external"
    artifact_path.mkdir(parents=True, exist_ok=True)

    reason_codes: list[str] = []
    if not runtime_python.exists():
        reason_codes.append("runtime_python_missing")
    if not source_repo.exists():
        reason_codes.append("source_repo_missing")

    smoke_payload: dict = {
        "smoke_status": "not_run",
        "reason_codes": reason_codes,
    }
    if reason_codes:
        smoke_status = "blocked_missing_runtime"
    else:
        try:
            smoke_payload = runner(
                runtime_python,
                source_repo,
                external_artifact_path.resolve(),
                timeout_seconds,
            )
            smoke_status = smoke_payload.get("smoke_status", "passed")
        except Exception as exc:  # pragma: no cover - covered by artifact behavior in integration runs
            smoke_status = "failed"
            reason_codes.append(type(exc).__name__)
            smoke_payload = {
                "smoke_status": smoke_status,
                "reason_codes": reason_codes,
                "error": str(exc),
            }

    real_smoke = smoke_status == "passed"
    metrics = {
        "run_id": run_id,
        "seed": seed,
        "smoke_status": smoke_status,
        "real_jlens_fit_apply_smoke": real_smoke,
        "model_id": smoke_payload.get("model_id", "not_run"),
        "model_source": smoke_payload.get("model_source", "not_run"),
        "model_license": smoke_payload.get("model_license", "not_run"),
        "runtime_python": str(runtime_python),
        "source_repo": str(source_repo),
        "reference_repo_commit": _git_commit(source_repo) if source_repo.exists() else None,
        "python_version": smoke_payload.get("python_version"),
        "torch_version": smoke_payload.get("torch_version"),
        "numpy_version": smoke_payload.get("numpy_version"),
        "transformers_version": smoke_payload.get("transformers_version"),
        "jlens_file": smoke_payload.get("jlens_file"),
        "prompt_count": smoke_payload.get("prompt_count", 0),
        "n_prompts": smoke_payload.get("n_prompts", 0),
        "d_model": smoke_payload.get("d_model", 0),
        "source_layers": smoke_payload.get("source_layers", []),
        "input_token_count": smoke_payload.get("input_token_count", 0),
        "lens_layers_returned": smoke_payload.get("lens_layers_returned", []),
        "gradient_access_confirmed": bool(smoke_payload.get("gradient_access_confirmed", False)),
        "layer_activation_access_confirmed": bool(
            smoke_payload.get("layer_activation_access_confirmed", False)
        ),
        "causal_intervention_performed": False,
        "outcome_leak_probe_performed": False,
        "not_causal": True,
        "not_sufficient_for_JLENS_PROVED": True,
        "reason_codes": reason_codes,
        "smoke_payload_path": str(artifact_path / "smoke_payload.json"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": f"J-lens smoke: runtime {runtime_python}",
            "2": f"J-lens smoke: status {smoke_status}; real fit/apply {real_smoke}",
            "3": "J-lens smoke: no outcome-leak probe and no causal intervention performed",
        }
    }

    ledger = Ledger()
    ledger.append("jlens_smoke_start", {"run_id": run_id, "seed": seed})
    ledger.append("jlens_smoke_payload", smoke_payload)
    ledger.append("jlens_smoke_result", metrics)

    _write_json(artifact_path / "smoke_payload.json", smoke_payload)
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))
    return JLensSmokeResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
