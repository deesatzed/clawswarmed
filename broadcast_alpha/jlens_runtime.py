import importlib.util
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path

from .jlens import JACOBIAN_LENS_COMMIT_SHA, JLENS_CRITICAL_LABELS, SOURCE_ACCESS_DATE
from .ledger import Ledger


BLACK_BOX_MODEL_SOURCES = {
    "anthropic",
    "claude",
    "gemini",
    "grok",
    "openai",
    "openrouter",
}
WHITE_BOX_MODEL_SOURCES = {
    "huggingface",
    "local_huggingface",
    "local",
}


@dataclass(frozen=True)
class JLensRuntimeReadinessResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _default_module_probe() -> dict[str, bool]:
    return {
        "torch": _module_available("torch"),
        "transformers": _module_available("transformers"),
        "jlens": _module_available("jlens"),
    }


def _tokenizer_label_check(
    labels: list[str],
    tokenizer_single_token: dict[str, bool] | None,
) -> dict:
    return {
        "check_method": (
            "runtime_tokenizer_override"
            if tokenizer_single_token is not None
            else "whitespace_shape_only_pending_runtime_tokenizer"
        ),
        "labels": {
            label: {
                "whitespace_single_token_shape": len(label.strip().split()) == 1,
                "single_token": (
                    bool(tokenizer_single_token.get(label, False))
                    if tokenizer_single_token is not None
                    else None
                ),
            }
            for label in labels
        },
        "all_labels_confirmed_single_token": (
            all(bool(tokenizer_single_token.get(label, False)) for label in labels)
            if tokenizer_single_token is not None
            else False
        ),
        "requires_selected_tokenizer": tokenizer_single_token is None,
    }


def _status_and_reasons(
    model_source: str,
    module_probe: dict[str, bool],
    label_check: dict,
    require_jacobian_lens: bool,
) -> tuple[str, list[str], bool, bool]:
    source = model_source.lower()
    reason_codes: list[str] = []

    if source in BLACK_BOX_MODEL_SOURCES:
        reason_codes.append("black_box_provider_rejected")
        return "blocked_black_box_provider", reason_codes, False, False

    if source not in WHITE_BOX_MODEL_SOURCES:
        reason_codes.append("unknown_model_source")

    if not module_probe.get("torch", False):
        reason_codes.append("torch_missing")
    if not module_probe.get("transformers", False):
        reason_codes.append("transformers_missing")
    if require_jacobian_lens and not module_probe.get("jlens", False):
        reason_codes.append("jacobian_lens_reference_missing")
    if not label_check["all_labels_confirmed_single_token"]:
        reason_codes.append("tokenizer_label_check_incomplete")

    dependency_preflight_passed = (
        source in WHITE_BOX_MODEL_SOURCES
        and module_probe.get("torch", False)
        and module_probe.get("transformers", False)
    )
    ready_for_fit_apply_smoke = (
        dependency_preflight_passed
        and (module_probe.get("jlens", False) or not require_jacobian_lens)
        and label_check["all_labels_confirmed_single_token"]
        and not reason_codes
    )

    if ready_for_fit_apply_smoke:
        return "ready_for_white_box_smoke", reason_codes, True, True
    if any(code.endswith("_missing") for code in reason_codes):
        return "blocked_missing_dependencies", reason_codes, dependency_preflight_passed, False
    return "blocked_incomplete_configuration", reason_codes, dependency_preflight_passed, False


def _result_card(run_id: str, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Run type: J-lens white-box runtime readiness

## Verdict

Readiness status: {metrics['readiness_status']}
White-box model available: {metrics['white_box_model_available']}
Gradient access confirmed: {metrics['gradient_access_confirmed']}
Real probe runnable: {metrics['real_probe_runnable']}

This is not a real J-lens probe. It records whether the local runtime is ready
for the first fit/apply smoke.

## Required Next Step

{metrics['next_required_step']}

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def prepare_jlens_probe(
    seed: int = 42,
    artifact_root: Path | None = None,
    model_id: str = "hf-internal-testing/tiny-random-gpt2",
    model_source: str = "huggingface",
    model_license: str | None = None,
    dtype: str = "float32",
    precision: str = "full",
    require_jacobian_lens: bool = True,
    module_probe: dict[str, bool] | None = None,
    tokenizer_single_token: dict[str, bool] | None = None,
) -> JLensRuntimeReadinessResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"jlens_runtime_readiness_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)

    module_probe = module_probe if module_probe is not None else _default_module_probe()
    label_check = _tokenizer_label_check(JLENS_CRITICAL_LABELS, tokenizer_single_token)
    readiness_status, reason_codes, dependency_preflight_passed, ready_for_fit_apply_smoke = _status_and_reasons(
        model_source=model_source,
        module_probe=module_probe,
        label_check=label_check,
        require_jacobian_lens=require_jacobian_lens,
    )
    source_lower = model_source.lower()
    white_box_model_available = False
    gradient_access_confirmed = False
    layer_activation_access_confirmed = False
    real_probe_runnable = False
    black_box_rejected = source_lower in BLACK_BOX_MODEL_SOURCES

    model_manifest = {
        "model_id": model_id,
        "model_source": model_source,
        "model_license": model_license or "unknown_not_yet_verified",
        "weight_source": model_source,
        "tokenizer": "not_loaded",
        "dtype": dtype,
        "precision": precision,
        "hardware": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        },
        "runtime_requirements": {
            "requires_open_weight_or_white_box_model": True,
            "requires_gradient_access": True,
            "requires_layer_activation_access": True,
            "requires_fitted_jacobian_lens": require_jacobian_lens,
            "black_box_api_models_allowed": False,
        },
        "module_probe": module_probe,
        "dependency_preflight_passed": dependency_preflight_passed,
        "jacobian_lens_reference": {
            "url": "https://github.com/anthropics/jacobian-lens",
            "commit_sha": JACOBIAN_LENS_COMMIT_SHA,
            "date_accessed": SOURCE_ACCESS_DATE,
            "installed_module_available": module_probe.get("jlens", False),
        },
        "black_box_provider_rejected": black_box_rejected,
        "gradient_access_confirmed": gradient_access_confirmed,
        "layer_activation_access_confirmed": layer_activation_access_confirmed,
    }
    next_required_step = (
        "Reject this provider for J-lens; choose a local/open-weight Hugging Face decoder."
        if black_box_rejected
        else "Install missing dependencies, verify tokenizer labels with the selected model, then run a fit/apply smoke."
    )
    metrics = {
        "run_id": run_id,
        "seed": seed,
        "readiness_status": readiness_status,
        "model_id": model_id,
        "model_source": model_source,
        "white_box_model_available": white_box_model_available,
        "dependency_preflight_passed": dependency_preflight_passed,
        "ready_for_fit_apply_smoke": ready_for_fit_apply_smoke,
        "gradient_access_confirmed": gradient_access_confirmed,
        "layer_activation_access_confirmed": layer_activation_access_confirmed,
        "real_probe_runnable": real_probe_runnable,
        "black_box_provider_rejected": black_box_rejected,
        "module_probe": module_probe,
        "tokenizer_labels_all_single_token": label_check["all_labels_confirmed_single_token"],
        "reason_codes": reason_codes,
        "evidence_class": "runtime_readiness",
        "not_activation_measurement": True,
        "not_causal": True,
        "not_sufficient_for_JLENS_PROVED": True,
        "model_manifest_path": str(artifact_path / "model_manifest.json"),
        "tokenizer_label_check_path": str(artifact_path / "tokenizer_label_check.json"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "replay_bundle_path": str(artifact_path / "replay"),
        "ledger_path": str(artifact_path / "ledger.jsonl"),
        "next_required_step": next_required_step,
    }
    replay_contexts = {
        "agent_1": {
            "1": f"J-lens runtime readiness: model {model_id} from {model_source}",
            "2": f"J-lens runtime readiness: {readiness_status}; real probe runnable {real_probe_runnable}",
            "3": "J-lens runtime readiness: no model weights loaded and no activation measurement performed",
        }
    }

    ledger = Ledger()
    ledger.append("jlens_runtime_start", {"run_id": run_id, "seed": seed, "model_id": model_id})
    ledger.append("jlens_model_manifest", model_manifest)
    ledger.append("jlens_tokenizer_label_check", label_check)
    ledger.append("jlens_runtime_readiness", metrics)

    _write_json(artifact_path / "model_manifest.json", model_manifest)
    _write_json(artifact_path / "tokenizer_label_check.json", label_check)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, metrics))

    return JLensRuntimeReadinessResult(
        run_id=run_id,
        artifact_path=artifact_path,
        expected_replay=replay_contexts,
    )
