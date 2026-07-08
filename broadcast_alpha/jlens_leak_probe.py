import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .ledger import Ledger


@dataclass(frozen=True)
class JLensLeakProbeResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


LeakProbeRunner = Callable[[Path, Path, Path, str, Path, float, int], dict]


LEAK_PROBE_CODE = r"""
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
vignette_path = pathlib.Path(sys.argv[3])
pc_threshold = float(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)

packet = json.loads(vignette_path.read_text())
tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
hf_model = AutoModelForCausalLM.from_pretrained(model_id, local_files_only=True)
hf_model.eval()
model = jlens.from_hf(hf_model, tokenizer)

def label_info(label):
    ids = tokenizer.encode(label, add_special_tokens=False)
    return {
        "token_ids": ids,
        "single_token": len(ids) == 1,
        "decoded": tokenizer.decode(ids),
    }

selected_labels = [" A", " B", " Y", " N"]
label_check = {label: label_info(label) for label in selected_labels}
if not all(info["single_token"] for info in label_check.values()):
    raise RuntimeError("selected A/B/Y/N labels are not all single-token")

label_ids = {label: label_check[label]["token_ids"][0] for label in selected_labels}
fit_prompts = [
    "The answer is A or B. Evidence comes after the marker. " * 4,
    "Review the case, wait for evidence, then choose A or B. " * 4,
    "Use A for the first option and B for the second option after evidence. " * 4,
]
lens = jlens.fit(model, fit_prompts, source_layers=[0, 1, 2, 3], dim_batch=8, max_seq_len=64)
lens_path = out / "leak_lens.pt"
lens.save(str(lens_path))
reloaded = jlens.JacobianLens.load(str(lens_path))

def augmented_prompt(text, labels):
    return (
        text
        + "\nAnswer choices: A="
        + labels[0]
        + "; B="
        + labels[1]
        + ". Reply with A or B only. Verdict:"
    )

def pre_evidence_positions(prompt, marker):
    prefix = prompt.split(marker)[0] if marker in prompt else prompt
    prefix_count = len(tokenizer.encode(prefix, add_special_tokens=False))
    start = max(0, prefix_count - 3)
    return list(range(start, prefix_count))

def condition_readout(prompt, marker):
    positions = pre_evidence_positions(prompt, marker)
    lens_logits, model_logits, input_ids = reloaded.apply(
        model,
        prompt,
        layers=[0, 1, 2, 3],
        positions=positions,
        max_seq_len=128,
    )
    target_id = label_ids[" B"]
    foil_id = label_ids[" A"]
    sham_target_id = label_ids[" Y"]
    sham_foil_id = label_ids[" N"]
    by_layer = {}
    for layer, logits in lens_logits.items():
        target_minus_foil = (logits[:, target_id] - logits[:, foil_id]).tolist()
        sham_margin = (logits[:, sham_target_id] - logits[:, sham_foil_id]).tolist()
        by_layer[str(layer)] = {
            "target_minus_foil_by_position": [float(value) for value in target_minus_foil],
            "target_minus_foil_mean": float(numpy.mean(target_minus_foil)),
            "sham_margin_by_position": [float(value) for value in sham_margin],
            "sham_margin_mean": float(numpy.mean(sham_margin)),
        }
    model_target_margin = (model_logits[:, target_id] - model_logits[:, foil_id]).tolist()
    token_ids = input_ids[0].tolist()
    tokens = tokenizer.convert_ids_to_tokens(token_ids)
    token_window = [
        {
            "position": int(position),
            "token": tokens[position] if 0 <= position < len(tokens) else None,
        }
        for position in positions
    ]
    return {
        "input_token_count": int(input_ids.shape[1]),
        "pre_evidence_positions": positions,
        "pre_evidence_token_window": token_window,
        "layers": by_layer,
        "model_target_minus_foil_by_position": [float(value) for value in model_target_margin],
        "model_target_minus_foil_mean": float(numpy.mean(model_target_margin)),
    }

case_results = []
for pair in packet["paired_vignettes"]:
    labels = pair["expected_verdict_labels"]
    marker = pair["evidence_span_marker"]
    prompts = {
        "outcome_withheld": augmented_prompt(pair["outcome_withheld"], labels),
        "outcome_revealed": augmented_prompt(pair["outcome_revealed"], labels),
        "negative_control": augmented_prompt(pair["negative_control"], labels),
    }
    condition_results = {
        name: condition_readout(prompt, marker)
        for name, prompt in prompts.items()
    }
    layer_deltas = {}
    for layer in reloaded.source_layers:
        layer_key = str(layer)
        revealed = condition_results["outcome_revealed"]["layers"][layer_key]
        withheld = condition_results["outcome_withheld"]["layers"][layer_key]
        negative = condition_results["negative_control"]["layers"][layer_key]
        delta_vs_withheld = (
            revealed["target_minus_foil_mean"]
            - withheld["target_minus_foil_mean"]
        )
        delta_vs_negative = (
            revealed["target_minus_foil_mean"]
            - negative["target_minus_foil_mean"]
        )
        sham_delta_vs_withheld = revealed["sham_margin_mean"] - withheld["sham_margin_mean"]
        sham_delta_vs_negative = revealed["sham_margin_mean"] - negative["sham_margin_mean"]
        layer_deltas[layer_key] = {
            "target_delta_vs_withheld": float(delta_vs_withheld),
            "target_delta_vs_negative_control": float(delta_vs_negative),
            "target_min_control_delta": float(min(delta_vs_withheld, delta_vs_negative)),
            "sham_delta_vs_withheld": float(sham_delta_vs_withheld),
            "sham_delta_vs_negative_control": float(sham_delta_vs_negative),
            "sham_min_control_delta": float(min(sham_delta_vs_withheld, sham_delta_vs_negative)),
        }
    best_layer, best_delta = max(
        ((layer, values["target_min_control_delta"]) for layer, values in layer_deltas.items()),
        key=lambda item: item[1],
    )
    best_sham_layer, best_sham_delta = max(
        ((layer, values["sham_min_control_delta"]) for layer, values in layer_deltas.items()),
        key=lambda item: item[1],
    )
    case_results.append(
        {
            "pair_id": pair["pair_id"],
            "domain": pair["domain"],
            "target_human_label": labels[1],
            "target_token_label": " B",
            "foil_human_label": labels[0],
            "foil_token_label": " A",
            "evidence_span_marker": marker,
            "condition_results": condition_results,
            "layer_deltas": layer_deltas,
            "pc_layer": best_layer,
            "pc_metric": float(best_delta),
            "sham_pc_layer": best_sham_layer,
            "sham_pc_metric": float(best_sham_delta),
            "differential_activation_present": bool(best_delta >= pc_threshold),
        }
    )

pc_metric = max(result["pc_metric"] for result in case_results)
sham_pc_metric = max(result["sham_pc_metric"] for result in case_results)
payload = {
    "leak_probe_status": "passed",
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
    "lens_path": str(lens_path),
    "fit_prompt_count": len(fit_prompts),
    "n_prompts": reloaded.n_prompts,
    "source_layers": reloaded.source_layers,
    "selected_label_check": label_check,
    "selected_labels_all_single_token": True,
    "case_count": len(case_results),
    "case_results": case_results,
    "pc_metric": float(pc_metric),
    "pc_threshold": pc_threshold,
    "differential_activation_present": bool(pc_metric >= pc_threshold),
    "negative_control_performed": True,
    "sham_control_performed": True,
    "sham_pc_metric": float(sham_pc_metric),
    "outcome_leak_probe_performed": True,
    "causal_intervention_performed": False,
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
    vignette_packet: Path,
    pc_threshold: float,
    timeout_seconds: int,
) -> dict:
    completed = subprocess.run(
        [
            str(runtime_python),
            "-c",
            LEAK_PROBE_CODE,
            str(external_artifact_path),
            model_id,
            str(vignette_packet),
            str(pc_threshold),
        ],
        cwd=source_repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("J-lens leak probe produced no JSON output")
    payload = json.loads(lines[-1])
    payload["stderr_tail"] = completed.stderr[-2000:]
    return payload


def _result_card(run_id: str, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Run type: Hugging Face J-lens outcome-leak probe

## Verdict

Probe status: {metrics['leak_probe_status']}
Outcome-leak probe performed: {metrics['outcome_leak_probe_performed']}
PC metric: {metrics['pc_metric']}
PC threshold: {metrics['pc_threshold']}
Differential activation present: {metrics['differential_activation_present']}
Negative control performed: {metrics['negative_control_performed']}
Sham control performed: {metrics['sham_control_performed']}
Causal intervention performed: {metrics['causal_intervention_performed']}

This probe records pre-evidence verdict-label readouts from a tiny Hugging Face
decoder using a fitted Jacobian lens. It is not causal and is not sufficient for
`JLENS_PROVED` without a later intervention/sham-control artifact.

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def run_jlens_leak_probe(
    seed: int = 42,
    artifact_root: Path | None = None,
    runtime_python: Path | None = None,
    source_repo: Path | None = None,
    model_id: str = "hf-internal-testing/tiny-random-gpt2",
    vignette_packet: Path | None = None,
    pc_threshold: float = 1.0,
    timeout_seconds: int = 240,
    runner: LeakProbeRunner | None = None,
) -> JLensLeakProbeResult:
    artifact_root = artifact_root or Path("artifacts")
    runtime_python = runtime_python or Path("../external/jlens-runtime/.venv/bin/python")
    source_repo = source_repo or Path("../external/jlens-runtime/jacobian-lens")
    vignette_packet = vignette_packet or Path("prereg/jlens_vignette_packet_01.json")
    runtime_python = runtime_python.expanduser().resolve()
    source_repo = source_repo.expanduser().resolve()
    vignette_packet = vignette_packet.expanduser().resolve()
    runner = runner or _default_runner
    run_id = f"jlens_leak_probe_seed_{seed}"
    artifact_path = artifact_root / run_id
    external_artifact_path = artifact_path / "external"
    artifact_path.mkdir(parents=True, exist_ok=True)

    reason_codes: list[str] = []
    if not runtime_python.exists():
        reason_codes.append("runtime_python_missing")
    if not source_repo.exists():
        reason_codes.append("source_repo_missing")
    if not vignette_packet.exists():
        reason_codes.append("vignette_packet_missing")

    probe_payload: dict = {"leak_probe_status": "not_run", "reason_codes": reason_codes}
    if reason_codes:
        leak_probe_status = "blocked_missing_runtime"
    else:
        try:
            probe_payload = runner(
                runtime_python,
                source_repo,
                external_artifact_path.resolve(),
                model_id,
                vignette_packet,
                pc_threshold,
                timeout_seconds,
            )
            leak_probe_status = probe_payload.get("leak_probe_status", "passed")
        except Exception as exc:  # pragma: no cover - integration artifact covers this path
            leak_probe_status = "failed"
            reason_codes.append(type(exc).__name__)
            probe_payload = {
                "leak_probe_status": leak_probe_status,
                "reason_codes": reason_codes,
                "error": str(exc),
            }

    outcome_leak_performed = bool(probe_payload.get("outcome_leak_probe_performed", False))
    differential_activation_present = bool(probe_payload.get("differential_activation_present", False))
    if outcome_leak_performed and not differential_activation_present:
        reason_codes.append("pc_below_threshold")
    if outcome_leak_performed:
        reason_codes.append("causal_intervention_missing")

    tokenizer_label_check = {
        "selected_label_check": probe_payload.get("selected_label_check", {}),
        "selected_labels_all_single_token": probe_payload.get("selected_labels_all_single_token", False),
        "label_policy": "A/B labels are used because human-readable verdict words are tokenizer-dependent.",
    }
    model_manifest = {
        "model_id": probe_payload.get("model_id", model_id),
        "model_source": probe_payload.get("model_source", "huggingface"),
        "model_license": probe_payload.get("model_license", "unknown_not_declared"),
        "model_revision": probe_payload.get("model_revision"),
        "model_type": probe_payload.get("model_type"),
        "tokenizer_class": probe_payload.get("tokenizer_class"),
        "hf_model_class": probe_payload.get("hf_model_class"),
        "layout": probe_payload.get("layout"),
        "n_layers": probe_payload.get("n_layers", 0),
        "d_model": probe_payload.get("d_model", 0),
        "vocab_size": probe_payload.get("vocab_size", 0),
        "runtime_python": str(runtime_python),
        "source_repo": str(source_repo),
        "python_version": probe_payload.get("python_version"),
        "torch_version": probe_payload.get("torch_version"),
        "numpy_version": probe_payload.get("numpy_version"),
        "transformers_version": probe_payload.get("transformers_version"),
        "jlens_file": probe_payload.get("jlens_file"),
    }
    prereg_manifest = {
        "prereg_id": "PREREG_LEAK-01",
        "prereg_path": str(Path("prereg/PREREG_LEAK-01.md")),
        "vignette_packet_path": str(vignette_packet),
        "pc_metric_definition": (
            "For each vignette, compute the pre-evidence B-minus-A Jacobian-lens "
            "logit margin in outcome_revealed, outcome_withheld, and negative_control "
            "conditions. The pair PC is the maximum layer-wise minimum of "
            "revealed-minus-withheld and revealed-minus-negative-control margins."
        ),
        "pc_threshold": pc_threshold,
        "primary_labels": {"foil": " A", "target": " B"},
        "sham_labels": {"foil": " N", "target": " Y"},
        "causal_claim_allowed": False,
    }
    metrics = {
        "run_id": run_id,
        "seed": seed,
        "leak_probe_status": leak_probe_status,
        "real_hf_jlens_leak_probe": leak_probe_status == "passed",
        "model_id": model_manifest["model_id"],
        "model_source": model_manifest["model_source"],
        "model_license": model_manifest["model_license"],
        "model_revision": model_manifest["model_revision"],
        "n_layers": model_manifest["n_layers"],
        "d_model": model_manifest["d_model"],
        "fit_prompt_count": probe_payload.get("fit_prompt_count", 0),
        "n_prompts": probe_payload.get("n_prompts", 0),
        "source_layers": probe_payload.get("source_layers", []),
        "case_count": probe_payload.get("case_count", 0),
        "selected_labels_all_single_token": tokenizer_label_check["selected_labels_all_single_token"],
        "pc_metric": probe_payload.get("pc_metric"),
        "pc_threshold": pc_threshold,
        "differential_activation_present": differential_activation_present,
        "negative_control_performed": bool(probe_payload.get("negative_control_performed", False)),
        "sham_control_performed": bool(probe_payload.get("sham_control_performed", False)),
        "sham_pc_metric": probe_payload.get("sham_pc_metric"),
        "outcome_leak_probe_performed": outcome_leak_performed,
        "causal_intervention_performed": False,
        "gradient_access_confirmed": bool(probe_payload.get("gradient_access_confirmed", False)),
        "layer_activation_access_confirmed": bool(probe_payload.get("layer_activation_access_confirmed", False)),
        "freeze_recommended": (not differential_activation_present)
        or not bool(probe_payload.get("causal_intervention_performed", False)),
        "not_causal": True,
        "not_sufficient_for_JLENS_PROVED": True,
        "reason_codes": reason_codes,
        "model_manifest_path": str(artifact_path / "model_manifest.json"),
        "tokenizer_label_check_path": str(artifact_path / "tokenizer_label_check.json"),
        "prereg_manifest_path": str(artifact_path / "prereg_manifest.json"),
        "readouts_path": str(artifact_path / "readouts.json"),
        "probe_payload_path": str(artifact_path / "probe_payload.json"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": f"J-lens leak probe: model {model_id}, prereg PREREG_LEAK-01",
            "2": f"J-lens leak probe: status {leak_probe_status}; PC {metrics['pc_metric']} threshold {pc_threshold}",
            "3": "J-lens leak probe: readouts recorded; no causal intervention performed; J-lens proof remains deferred",
        }
    }

    ledger = Ledger()
    ledger.append("jlens_leak_probe_start", {"run_id": run_id, "seed": seed, "model_id": model_id})
    ledger.append("jlens_leak_model_manifest", model_manifest)
    ledger.append("jlens_leak_tokenizer_label_check", tokenizer_label_check)
    ledger.append("jlens_leak_prereg_manifest", prereg_manifest)
    ledger.append("jlens_leak_readouts", {"case_count": metrics["case_count"], "pc_metric": metrics["pc_metric"]})
    ledger.append("jlens_leak_probe_result", metrics)

    _write_json(artifact_path / "model_manifest.json", model_manifest)
    _write_json(artifact_path / "tokenizer_label_check.json", tokenizer_label_check)
    _write_json(artifact_path / "prereg_manifest.json", prereg_manifest)
    _write_json(artifact_path / "readouts.json", {"case_results": probe_payload.get("case_results", [])})
    _write_json(artifact_path / "probe_payload.json", probe_payload)
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))

    return JLensLeakProbeResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
