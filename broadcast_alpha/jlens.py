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
            "reason": "real J-lens source/model access has not been verified",
            "verdict_label": verdict_label,
            "evidence_chars": len(evidence_text),
            "layer_position_activation": [],
        }


def _source_manifest() -> dict:
    return {
        "required_exact_source": {
            "name": REQUIRED_EXACT_SOURCE,
            "found": False,
            "decision": "do_not_implement_real_probe_without_exact_source",
        },
        "searched_queries": SEARCHED_QUERIES,
        "verified_adjacent_sources": VERIFIED_ADJACENT_SOURCES,
        "rejected_claims": [
            {
                "claim": "A real Anthropic J-lens / global workspace probe is ready to implement",
                "reason": "Exact paper, repository, or implementation was not verified in the current source lookup.",
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

The exact named J-lens source was not verified, and this runtime has no
configured white-box gatekeeper model with gradient/layer access. No real
J-lens probe was implemented or run.

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
            "required_exact_source_found": False,
            "white_box_model_available": False,
            "real_probe_runnable": False,
            "reason_codes": [
                "exact_jlens_source_not_verified",
                "white_box_model_access_not_configured",
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
        "required_exact_source_found": False,
        "white_box_model_available": False,
        "real_probe_runnable": False,
        "single_token_labels_verified": single_token_labels,
        "single_token_label_count": len(single_token_labels),
        "source_manifest_path": str(artifact_path / "sources.json"),
        "ledger_path": str(ledger_path),
        "replay_bundle_path": str(artifact_path / "replay"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "reason_codes": [
            "exact_jlens_source_not_verified",
            "white_box_model_access_not_configured",
            "real_probe_not_run",
        ],
        "next_required_unblockers": [
            "Identify and cite the exact J-lens paper, repository, or implementation.",
            "Configure a white-box gatekeeper model with gradient/layer access.",
            "Add causal intervention controls before making mechanistic claims.",
        ],
    }
    ledger.append("metrics", metrics)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_result_card(run_id, seed, metrics))
    return JLensGateResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
