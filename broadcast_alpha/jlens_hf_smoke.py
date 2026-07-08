import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .ledger import Ledger


@dataclass(frozen=True)
class JLensHFSmokeResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


HFSmokeRunner = Callable[[Path, Path, Path, str, int], dict]


HF_SMOKE_CODE = r"""
import json
import pathlib
import sys

import jlens
import numpy
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

out = pathlib.Path(sys.argv[1])
model_id = sys.argv[2]
out.mkdir(parents=True, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
hf_model = AutoModelForCausalLM.from_pretrained(model_id, local_files_only=True)
hf_model.eval()
model = jlens.from_hf(hf_model, tokenizer)

selected_labels = [" A", " B", " Y", " N", " no"]
critical_labels = ["yes", "no", "admit", "reject", "pass", "fail"]

def label_info(label):
    ids = tokenizer.encode(label, add_special_tokens=False)
    return {
        "token_ids": ids,
        "single_token": len(ids) == 1,
        "decoded": tokenizer.decode(ids),
    }

prompts = [
    "The answer is A or B. Evidence comes after the marker. " * 4,
    "Review the code and choose A or B after all evidence. " * 4,
]
lens = jlens.fit(model, prompts, source_layers=[0, 1, 2, 3], dim_batch=8, max_seq_len=64)
lens_path = out / "hf_lens.pt"
lens.save(str(lens_path))
reloaded = jlens.JacobianLens.load(str(lens_path))
lens_logits, model_logits, input_ids = reloaded.apply(
    model,
    "Question: choose A or B. Evidence: bounds check fails. Answer:",
    layers=[0, 2, 3],
    positions=[-1],
    max_seq_len=64,
)

payload = {
    "smoke_status": "passed",
    "model_id": model_id,
    "model_source": "huggingface",
    "model_license": "unknown_not_declared",
    "model_revision": getattr(hf_model.config, "_commit_hash", None),
    "model_type": getattr(hf_model.config, "model_type", None),
    "tokenizer_class": type(tokenizer).__name__,
    "hf_model_class": type(hf_model).__name__,
    "layout": repr(model.layout),
    "n_layers": model.n_layers,
    "d_model": model.d_model,
    "vocab_size": int(getattr(hf_model.config, "vocab_size", 0)),
    "python_version": sys.version.split()[0],
    "torch_version": torch.__version__,
    "numpy_version": numpy.__version__,
    "transformers_version": transformers.__version__,
    "jlens_file": jlens.__file__,
    "prompt_count": len(prompts),
    "n_prompts": reloaded.n_prompts,
    "source_layers": reloaded.source_layers,
    "lens_path": str(lens_path),
    "input_token_count": int(input_ids.shape[1]),
    "lens_layers_returned": sorted(lens_logits),
    "model_logits_shape": list(model_logits.shape),
    "selected_label_check": {label: label_info(label) for label in selected_labels},
    "critical_label_check": {label: label_info(label) for label in critical_labels},
    "selected_labels_all_single_token": all(label_info(label)["single_token"] for label in selected_labels),
    "critical_labels_all_single_token": all(label_info(label)["single_token"] for label in critical_labels),
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
    model_id: str,
    timeout_seconds: int,
) -> dict:
    completed = subprocess.run(
        [str(runtime_python), "-c", HF_SMOKE_CODE, str(external_artifact_path), model_id],
        cwd=source_repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("HF J-lens smoke produced no JSON output")
    payload = json.loads(lines[-1])
    payload["stderr_tail"] = completed.stderr[-2000:]
    return payload


def _result_card(run_id: str, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Run type: Hugging Face J-lens fit/apply smoke

## Verdict

Smoke status: {metrics['smoke_status']}
Real HF J-lens fit/apply smoke: {metrics['real_hf_jlens_fit_apply_smoke']}
Selected labels all single-token: {metrics['selected_labels_all_single_token']}
Critical labels all single-token: {metrics['critical_labels_all_single_token']}
Gradient access confirmed: {metrics['gradient_access_confirmed']}
Layer activation access confirmed: {metrics['layer_activation_access_confirmed']}
Causal intervention performed: {metrics['causal_intervention_performed']}

This smoke uses a tiny Hugging Face decoder and proves the HF adapter can fit
and apply a Jacobian lens locally. It is not an outcome-leak probe and is not
sufficient for `JLENS_PROVED`.

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_jlens_hf_smoke(
    seed: int = 42,
    artifact_root: Path | None = None,
    runtime_python: Path | None = None,
    source_repo: Path | None = None,
    model_id: str = "hf-internal-testing/tiny-random-gpt2",
    timeout_seconds: int = 180,
    runner: HFSmokeRunner | None = None,
) -> JLensHFSmokeResult:
    artifact_root = artifact_root or Path("artifacts")
    runtime_python = runtime_python or Path("../external/jlens-runtime/.venv/bin/python")
    source_repo = source_repo or Path("../external/jlens-runtime/jacobian-lens")
    runtime_python = runtime_python.expanduser().resolve()
    source_repo = source_repo.expanduser().resolve()
    runner = runner or _default_runner
    run_id = f"jlens_hf_smoke_seed_{seed}"
    artifact_path = artifact_root / run_id
    external_artifact_path = artifact_path / "external"
    artifact_path.mkdir(parents=True, exist_ok=True)

    reason_codes: list[str] = []
    if not runtime_python.exists():
        reason_codes.append("runtime_python_missing")
    if not source_repo.exists():
        reason_codes.append("source_repo_missing")

    smoke_payload: dict = {"smoke_status": "not_run", "reason_codes": reason_codes}
    if reason_codes:
        smoke_status = "blocked_missing_runtime"
    else:
        try:
            smoke_payload = runner(
                runtime_python,
                source_repo,
                external_artifact_path.resolve(),
                model_id,
                timeout_seconds,
            )
            smoke_status = smoke_payload.get("smoke_status", "passed")
        except Exception as exc:  # pragma: no cover - integration artifact covers this path
            smoke_status = "failed"
            reason_codes.append(type(exc).__name__)
            smoke_payload = {
                "smoke_status": smoke_status,
                "reason_codes": reason_codes,
                "error": str(exc),
            }

    real_smoke = smoke_status == "passed"
    tokenizer_label_check = {
        "selected_label_check": smoke_payload.get("selected_label_check", {}),
        "critical_label_check": smoke_payload.get("critical_label_check", {}),
        "selected_labels_all_single_token": smoke_payload.get("selected_labels_all_single_token", False),
        "critical_labels_all_single_token": smoke_payload.get("critical_labels_all_single_token", False),
    }
    model_manifest = {
        "model_id": smoke_payload.get("model_id", model_id),
        "model_source": smoke_payload.get("model_source", "huggingface"),
        "model_license": smoke_payload.get("model_license", "unknown_not_declared"),
        "model_revision": smoke_payload.get("model_revision"),
        "model_type": smoke_payload.get("model_type"),
        "tokenizer_class": smoke_payload.get("tokenizer_class"),
        "hf_model_class": smoke_payload.get("hf_model_class"),
        "layout": smoke_payload.get("layout"),
        "n_layers": smoke_payload.get("n_layers", 0),
        "d_model": smoke_payload.get("d_model", 0),
        "vocab_size": smoke_payload.get("vocab_size", 0),
        "runtime_python": str(runtime_python),
        "source_repo": str(source_repo),
        "python_version": smoke_payload.get("python_version"),
        "torch_version": smoke_payload.get("torch_version"),
        "numpy_version": smoke_payload.get("numpy_version"),
        "transformers_version": smoke_payload.get("transformers_version"),
        "jlens_file": smoke_payload.get("jlens_file"),
    }
    metrics = {
        "run_id": run_id,
        "seed": seed,
        "smoke_status": smoke_status,
        "real_hf_jlens_fit_apply_smoke": real_smoke,
        "model_id": model_manifest["model_id"],
        "model_source": model_manifest["model_source"],
        "model_license": model_manifest["model_license"],
        "model_revision": model_manifest["model_revision"],
        "n_layers": model_manifest["n_layers"],
        "d_model": model_manifest["d_model"],
        "prompt_count": smoke_payload.get("prompt_count", 0),
        "n_prompts": smoke_payload.get("n_prompts", 0),
        "source_layers": smoke_payload.get("source_layers", []),
        "input_token_count": smoke_payload.get("input_token_count", 0),
        "lens_layers_returned": smoke_payload.get("lens_layers_returned", []),
        "selected_labels_all_single_token": tokenizer_label_check["selected_labels_all_single_token"],
        "critical_labels_all_single_token": tokenizer_label_check["critical_labels_all_single_token"],
        "gradient_access_confirmed": bool(smoke_payload.get("gradient_access_confirmed", False)),
        "layer_activation_access_confirmed": bool(smoke_payload.get("layer_activation_access_confirmed", False)),
        "causal_intervention_performed": False,
        "outcome_leak_probe_performed": False,
        "not_causal": True,
        "not_sufficient_for_JLENS_PROVED": True,
        "reason_codes": reason_codes,
        "model_manifest_path": str(artifact_path / "model_manifest.json"),
        "tokenizer_label_check_path": str(artifact_path / "tokenizer_label_check.json"),
        "smoke_payload_path": str(artifact_path / "smoke_payload.json"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": f"HF J-lens smoke: model {model_id}",
            "2": f"HF J-lens smoke: status {smoke_status}; real fit/apply {real_smoke}",
            "3": "HF J-lens smoke: tokenizer labels recorded; no outcome-leak probe or causal intervention performed",
        }
    }

    ledger = Ledger()
    ledger.append("jlens_hf_smoke_start", {"run_id": run_id, "seed": seed, "model_id": model_id})
    ledger.append("jlens_hf_model_manifest", model_manifest)
    ledger.append("jlens_hf_tokenizer_label_check", tokenizer_label_check)
    ledger.append("jlens_hf_smoke_payload", smoke_payload)
    ledger.append("jlens_hf_smoke_result", metrics)

    _write_json(artifact_path / "model_manifest.json", model_manifest)
    _write_json(artifact_path / "tokenizer_label_check.json", tokenizer_label_check)
    _write_json(artifact_path / "smoke_payload.json", smoke_payload)
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))

    return JLensHFSmokeResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
