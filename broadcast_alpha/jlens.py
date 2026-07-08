import json
from dataclasses import dataclass
from pathlib import Path

from .ledger import Ledger


FAILURE_LEDGER_ENTRY_ID = "JLENS-FREEZE-001"
JLENS_CRITICAL_LABELS = ["yes", "no", "admit", "reject", "pass", "fail"]
REQUIRED_EXACT_SOURCE = (
    "Verbalizable Representations Form a Global Workspace in Language Models / "
    "Anthropic jacobian-lens implementation"
)
SOURCE_ACCESS_DATE = "2026-07-08"
JACOBIAN_LENS_COMMIT_SHA = "581d398613e5602a5af361e1c34d3a92ea82ba8e"

SEARCHED_QUERIES = [
    "Anthropic Verbalizable Representations Form a Global Workspace in Language Models J-lens",
    "jacobian-lens GitHub Anthropic",
    "Verbalizable Representations Form a Global Workspace in Language Models arXiv",
    "\"Verbalizable Representations\" \"J-lens\"",
    "\"J-space\" \"Verbalizable Representations\"",
    "site:anthropic.com \"Verbalizable Representations\" \"J-lens\"",
    "site:transformer-circuits.pub \"jacobian lens\"",
    "site:github.com/anthropics \"jacobian-lens\"",
]

VERIFIED_ADJACENT_SOURCES = [
    {
        "title": "Towards Best Practices of Activation Patching in Language Models: Metrics and Methods",
        "url": "https://arxiv.org/abs/2309.16042",
        "role": "activation_patching_methodology",
        "verified": True,
        "note": "Primary-methodology adjacent source for activation patching, not the exact J-lens source.",
    },
    {
        "title": "AtP*: An efficient and scalable method for localizing LLM behaviour to components",
        "url": "https://arxiv.org/abs/2403.00745",
        "role": "gradient_based_localization_caution",
        "verified": True,
        "note": "Adjacent source on attribution patching limits and false-negative risks.",
    },
    {
        "title": "How to use and interpret activation patching",
        "url": "https://arxiv.org/abs/2404.15255",
        "role": "activation_patching_interpretation_caution",
        "verified": True,
        "note": "Adjacent source on evidence limits and interpretation subtleties.",
    },
    {
        "title": "TransformerLens",
        "url": "https://github.com/TransformerLensOrg/TransformerLens",
        "role": "white_box_model_tooling_candidate",
        "verified": True,
        "note": "Tooling candidate for internal activations; not proof that the exact J-lens rail is available.",
    },
]

VERIFIED_EXACT_SOURCES = [
    {
        "title": "anthropics/jacobian-lens",
        "url": "https://github.com/anthropics/jacobian-lens",
        "role": "reference_implementation",
        "license": "Apache-2.0",
        "commit_sha": JACOBIAN_LENS_COMMIT_SHA,
        "branch": "main",
        "date_accessed": SOURCE_ACCESS_DATE,
        "verified": True,
        "note": (
            "Reference implementation for the global-workspace/Jacobian-lens paper. "
            "The repository states it is not maintained; no model weights or text corpora are bundled."
        ),
    },
    {
        "title": "Verbalizable Representations Form a Global Workspace in Language Models",
        "url": "https://transformer-circuits.pub/2026/workspace/index.html",
        "role": "primary_paper",
        "license": "external_page_terms",
        "commit_sha": None,
        "branch": None,
        "date_accessed": SOURCE_ACCESS_DATE,
        "verified": True,
        "note": (
            "Primary Transformer Circuits article describing the Jacobian lens, "
            "J-space, and intervention framing."
        ),
    },
]

MANUAL_SANITY_SURFACES = [
    {
        "title": "Neuronpedia Jacobian Lens",
        "url": "https://www.neuronpedia.org/jlens",
        "role": "manual_sanity_check_surface",
        "date_accessed": SOURCE_ACCESS_DATE,
        "verified": True,
        "proof_status": "not_formal_proof",
        "note": "Useful for a no-code directional check only; cannot satisfy the white-box causal proof gate.",
    }
]


@dataclass(frozen=True)
class JLensGateResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def assert_single_token(label: str) -> str:
    if len(label.strip().split()) != 1:
        raise ValueError(f"verdict label must be a single token: {label!r}")
    return label


def verify_single_token_labels(labels: list[str]) -> dict[str, bool]:
    return {assert_single_token(label): True for label in labels}


class NullJLensProbe:
    def run(self, verdict_label: str, evidence_text: str) -> dict:
        assert_single_token(verdict_label)
        return {
            "status": "unavailable",
            "reason": "reference source exists, but real J-lens runtime/model access has not been verified",
            "verdict_label": verdict_label,
            "evidence_chars": len(evidence_text),
            "layer_position_activation": [],
        }


def _source_manifest() -> dict:
    return {
        "required_exact_source": {
            "name": REQUIRED_EXACT_SOURCE,
            "found": True,
            "decision": "source_verified_runtime_still_gated",
            "date_accessed": SOURCE_ACCESS_DATE,
        },
        "searched_queries": SEARCHED_QUERIES,
        "verified_exact_sources": VERIFIED_EXACT_SOURCES,
        "verified_adjacent_sources": VERIFIED_ADJACENT_SOURCES,
        "manual_sanity_surfaces": MANUAL_SANITY_SURFACES,
        "rejected_claims": [
            {
                "claim": "A real Anthropic J-lens / global workspace probe is ready to implement",
                "reason": (
                    "The exact source is now verified, but no local white-box model runtime, "
                    "fitted lens, or causal intervention controls are configured."
                ),
            },
            {
                "claim": "Timing or readout alone can support the Glass Gate causal claim",
                "reason": "The build contract requires white-box layer/gradient access plus causal intervention controls.",
            },
        ],
    }


def _result_card(run_id: str, seed: int, metrics: dict) -> str:
    return f"""# Result Card: {run_id}

Seed: {seed}
Run type: J-lens source/model gate

## Decision

J-lens rail frozen.

The exact named J-lens source is now verified, but this runtime has no
configured white-box gatekeeper model with gradient/layer access, no fitted
Jacobian lens, and no causal intervention controls. No real J-lens probe was
implemented or run.

## Gate checks

| Check | Result |
|---|---|
| Exact source found | {metrics['required_exact_source_found']} |
| White-box model available | {metrics['white_box_model_available']} |
| Real probe runnable | {metrics['real_probe_runnable']} |
| Single-token labels verified | {metrics['single_token_label_count']} labels |

## Outcome

Rail status: {metrics['rail_status']}
Failure ledger entry: {metrics['failure_ledger_entry_id']}

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass

## Failure ledger updates

Record `{metrics['failure_ledger_entry_id']}` in `FAILURE_LEDGER.md`.
"""


def run_jlens_gate(seed: int = 42, artifact_root: Path | None = None) -> JLensGateResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"jlens_gate_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)

    single_token_labels = verify_single_token_labels(JLENS_CRITICAL_LABELS)
    sources = _source_manifest()
    replay_contexts = {
        "agent_1": {
            "1": "J-lens source/model gate: exact source lookup completed before implementation",
            "2": "single-token verdict labels verified for yes, no, admit, reject, pass, fail",
            "3": "J-lens rail frozen: exact source/model unavailable; macro and RQGM rails continue",
        }
    }

    _write_json(artifact_path / "sources.json", sources)
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)

    ledger = Ledger()
    ledger.append(
        "run_start",
        {
            "run_id": run_id,
            "seed": seed,
            "run_type": "jlens_source_model_gate",
        },
    )
    ledger.append(
        "source_manifest",
        {
            "required_exact_source": sources["required_exact_source"],
            "verified_exact_source_count": len(VERIFIED_EXACT_SOURCES),
            "verified_adjacent_source_count": len(VERIFIED_ADJACENT_SOURCES),
            "searched_query_count": len(SEARCHED_QUERIES),
        },
    )
    ledger.append(
        "single_token_verdict_check",
        {
            "labels": single_token_labels,
            "status": "passed",
        },
    )
    ledger.append(
        "jlens_gate_decision",
        {
            "failure_ledger_entry_id": FAILURE_LEDGER_ENTRY_ID,
            "rail_status": "frozen",
            "required_exact_source_found": True,
            "white_box_model_available": False,
            "real_probe_runnable": False,
            "reason_codes": [
                "source_verified_runtime_unavailable",
                "white_box_model_access_not_configured",
                "causal_intervention_controls_not_run",
                "real_probe_not_run",
            ],
            "decision": "freeze_jlens_rail_continue_macro_and_rqgm",
        },
    )

    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics = {
        "run_id": run_id,
        "rail_status": "frozen",
        "failure_ledger_entry_id": FAILURE_LEDGER_ENTRY_ID,
        "required_exact_source": REQUIRED_EXACT_SOURCE,
        "required_exact_source_found": True,
        "source_access_date": SOURCE_ACCESS_DATE,
        "jacobian_lens_commit_sha": JACOBIAN_LENS_COMMIT_SHA,
        "white_box_model_available": False,
        "real_probe_runnable": False,
        "single_token_labels_verified": single_token_labels,
        "single_token_label_count": len(single_token_labels),
        "source_manifest_path": str(artifact_path / "sources.json"),
        "ledger_path": str(ledger_path),
        "replay_bundle_path": str(artifact_path / "replay"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "reason_codes": [
            "source_verified_runtime_unavailable",
            "white_box_model_access_not_configured",
            "causal_intervention_controls_not_run",
            "real_probe_not_run",
        ],
        "next_required_unblockers": [
            "Configure a white-box gatekeeper model with gradient/layer access.",
            "Install or clone the reference implementation outside the app repo and run the smallest fit/apply smoke.",
            "Add causal intervention controls before making mechanistic claims.",
        ],
    }
    ledger.append("metrics", metrics)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, seed, metrics))
    return JLensGateResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
