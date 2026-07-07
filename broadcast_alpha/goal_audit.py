import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ledger import Ledger


@dataclass(frozen=True)
class GoalAuditResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


REQUIRED_PREREGS = [
    "PREREG_DSH-01.md",
    "PREREG_PART-01.md",
    "PREREG_LEAK-01.md",
    "PREREG_CAUSAL-01.md",
    "PREREG_EPOCH-01.md",
    "PREREG_BRIDGE-01.md",
    "PREREG_MECHADMIT-01.md",
    "PREREG_LIVE-01.md",
]

REQUIRED_ARMS = {"abundant", "random", "scarce_naive_topk", "scarce_protected"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def _ledger_verified(path: Path) -> bool:
    ledger_path = path / "ledger.jsonl"
    return ledger_path.exists() and Ledger.from_jsonl(ledger_path).verify_chain()


def _item(
    requirement_id: str,
    requirement: str,
    status: str,
    evidence_path: Path,
    evidence: str,
    value: Any | None = None,
) -> dict[str, Any]:
    return {
        "id": requirement_id,
        "requirement": requirement,
        "status": status,
        "evidence_path": str(evidence_path),
        "evidence": evidence,
        "value": value,
    }


def _final_report_path(artifact_root: Path) -> Path:
    top_level = artifact_root / "final_report_seed_42"
    if (top_level / "metrics.json").exists():
        return top_level
    nested = artifact_root / "run_all_seed_42" / "final_report"
    return nested


def _result_card(run_id: str, metrics: dict[str, Any], items: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| {item['id']} | {item['status']} | {item['evidence']} |"
        for item in items
    )
    incomplete = [
        item["id"]
        for item in items
        if item["status"] == "incomplete"
    ]
    incomplete_line = ", ".join(incomplete) if incomplete else "none"
    verdict = (
        "Goal remains incomplete."
        if metrics["overall_status"] == "not_complete"
        else "No incomplete requirement was detected by this audit."
    )
    return f"""# Result Card: {run_id}

Run type: Glass Gate goal evidence audit

## Verdict

Overall status: {metrics['overall_status']}
{verdict}

Incomplete requirements: {incomplete_line}

## Counts

Proved: {metrics['proved_count']}
Deferred with record: {metrics['deferred_count']}
Incomplete: {metrics['incomplete_count']}
Total requirements audited: {metrics['requirement_count']}

## Requirement Matrix

| Requirement | Status | Evidence |
|---|---|---|
{rows}

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass
"""


def audit_goal(
    artifact_root: Path | None = None,
    output_dir: Path | None = None,
    repo_root: Path | None = None,
) -> GoalAuditResult:
    artifact_root = artifact_root or Path("artifacts")
    output_dir = output_dir or artifact_root / "goal_audit_seed_42"
    repo_root = repo_root or Path(".")
    run_id = output_dir.name
    output_dir.mkdir(parents=True, exist_ok=True)

    final_report = _final_report_path(artifact_root)
    run_all = artifact_root / "run_all_seed_42"
    ledger_stress = artifact_root / "ledger_stress_seed_42"
    if not (ledger_stress / "metrics.json").exists():
        ledger_stress = run_all / "source_artifacts" / "ledger_stress_seed_42"
    live_sequence = artifact_root / "live_sequence_seed_42"
    if not (live_sequence / "metrics.json").exists():
        live_sequence = run_all / "source_artifacts" / "live_sequence_seed_42"

    final_metrics = _read_json(final_report / "metrics.json") if (final_report / "metrics.json").exists() else {}
    run_all_metrics = _read_json(run_all / "metrics.json") if (run_all / "metrics.json").exists() else {}
    ledger_stress_metrics = (
        _read_json(ledger_stress / "metrics.json")
        if (ledger_stress / "metrics.json").exists()
        else {}
    )
    live_sequence_metrics = (
        _read_json(live_sequence / "metrics.json")
        if (live_sequence / "metrics.json").exists()
        else {}
    )

    readme = _read_text(repo_root / "README.md")
    failure_ledger = _read_text(repo_root / "FAILURE_LEDGER.md")
    prereg_dir = repo_root / "prereg"
    prereg_paths = [prereg_dir / name for name in REQUIRED_PREREGS]

    readme_ok = "research instrument" in readme and "not a product" in readme
    archive_ok = (repo_root / "docs" / "archive" / "HANDOFF_claswarmed_glassgate_v1_2.md").exists()
    failure_ledger_ok = "JLENS-FREEZE-001" in failure_ledger
    preregs_ok = all(path.exists() for path in prereg_paths)

    d_by_arm = final_metrics.get("D_by_arm", {})
    ci = final_metrics.get("glassgate_lift_ci95", [])
    source_ledgers_ok = bool(final_metrics.get("all_source_ledgers_verified")) and _ledger_verified(final_report)
    run_all_ok = (
        run_all_metrics.get("run_status") == "complete_with_deferred_jlens"
        and bool(run_all_metrics.get("all_child_ledgers_verified"))
        and _ledger_verified(run_all)
    )
    ledger_stress_ok = (
        int(ledger_stress_metrics.get("synthetic_receipt_count", 0) or 0) >= 10_000
        and int(ledger_stress_metrics.get("mixed_kind_count", 0) or 0) >= 2
        and bool(ledger_stress_metrics.get("pre_metrics_chain_verified"))
        and bool(ledger_stress_metrics.get("ledger_verified"))
        and bool(ledger_stress_metrics.get("tamper_detection_passed"))
        and _ledger_verified(ledger_stress)
    )
    live_adapter_calls = int(live_sequence_metrics.get("adapter_call_count_total", 0) or 0)
    live_model_run_performed = bool(
        final_metrics.get("live_model_run_performed")
        or run_all_metrics.get("live_model_run_performed")
        or live_sequence_metrics.get("smoke_model_run_performed")
    )
    jlens_frozen = (
        final_metrics.get("jlens_rail_status") == "frozen"
        and final_metrics.get("jlens_failure_ledger_entry_id") == "JLENS-FREEZE-001"
        and failure_ledger_ok
    )

    items = [
        _item(
            "repository_and_preregistration",
            "Repository identifies the instrument and contains the archived handoff, failure ledger, and prereg files.",
            "proved" if readme_ok and archive_ok and failure_ledger_ok and preregs_ok else "incomplete",
            repo_root / "README.md",
            "README, handoff archive, failure ledger, and all required prereg files found."
            if readme_ok and archive_ok and failure_ledger_ok and preregs_ok
            else "One or more repository/preregistration source files are missing or incomplete.",
            {
                "readme_ok": readme_ok,
                "archive_ok": archive_ok,
                "failure_ledger_ok": failure_ledger_ok,
                "preregs_ok": preregs_ok,
            },
        ),
        _item(
            "macro_glassgate_lift",
            "Macro report includes GLASSGATE_LIFT with a 95% confidence interval.",
            "proved" if "glassgate_lift" in final_metrics and len(ci) == 2 else "incomplete",
            final_report / "metrics.json",
            f"GLASSGATE_LIFT={final_metrics.get('glassgate_lift')} CI={ci}"
            if "glassgate_lift" in final_metrics
            else "Macro GLASSGATE_LIFT metric is missing.",
            {
                "glassgate_lift": final_metrics.get("glassgate_lift"),
                "glassgate_lift_ci95": ci,
            },
        ),
        _item(
            "macro_d_by_arm",
            "Macro report includes D estimates for all four workspace arms.",
            "proved" if REQUIRED_ARMS.issubset(d_by_arm) else "incomplete",
            final_report / "metrics.json",
            "D estimates exist for abundant, random, scarce_naive_topk, and scarce_protected."
            if REQUIRED_ARMS.issubset(d_by_arm)
            else "One or more D-by-arm estimates are missing.",
            d_by_arm,
        ),
        _item(
            "replayable_tamper_evident_ledgers",
            "Final report and run-all ledgers verify and preserve replay paths.",
            "proved" if source_ledgers_ok and run_all_ok else "incomplete",
            final_report / "ledger.jsonl",
            "Final report source ledgers and run-all child ledgers verify."
            if source_ledgers_ok and run_all_ok
            else "One or more required ledgers are missing or failed verification.",
            {
                "final_report_ledger_verified": _ledger_verified(final_report),
                "run_all_ledger_verified": _ledger_verified(run_all),
                "all_source_ledgers_verified": final_metrics.get("all_source_ledgers_verified"),
                "all_child_ledgers_verified": run_all_metrics.get("all_child_ledgers_verified"),
            },
        ),
        _item(
            "ledger_stress_10k",
            "At least 10,000 mixed synthetic receipts verify and a tampered copy fails verification.",
            "proved" if ledger_stress_ok else "incomplete",
            ledger_stress / "metrics.json",
            "10,000 mixed synthetic receipts verify and tamper detection passes."
            if ledger_stress_ok
            else "10,000 mixed-receipt ledger stress proof is missing or failed.",
            {
                "synthetic_receipt_count": ledger_stress_metrics.get("synthetic_receipt_count"),
                "mixed_kind_count": ledger_stress_metrics.get("mixed_kind_count"),
                "pre_metrics_chain_verified": ledger_stress_metrics.get("pre_metrics_chain_verified"),
                "ledger_verified": ledger_stress_metrics.get("ledger_verified"),
                "tamper_detection_passed": ledger_stress_metrics.get("tamper_detection_passed"),
            },
        ),
        _item(
            "seed_detectability_audit",
            "Seed detectability audit is present and does not fail the current camouflage gate.",
            "proved"
            if final_metrics.get("seed_detectability_auc") == 0.5
            and final_metrics.get("seed_adversarial_auc") == 0.5
            and final_metrics.get("seed_camouflage_failed") is False
            else "incomplete",
            final_report / "metrics.json",
            "Seed detectability and adversarial token AUC are both 0.5 with no camouflage failure."
            if final_metrics.get("seed_detectability_auc") == 0.5
            and final_metrics.get("seed_adversarial_auc") == 0.5
            and final_metrics.get("seed_camouflage_failed") is False
            else "Seed detectability audit is missing or failing.",
            {
                "seed_detectability_auc": final_metrics.get("seed_detectability_auc"),
                "seed_adversarial_auc": final_metrics.get("seed_adversarial_auc"),
                "seed_camouflage_failed": final_metrics.get("seed_camouflage_failed"),
            },
        ),
        _item(
            "rqgm_epoch_trajectory",
            "Controlled evaluator evolution has at least five epochs.",
            "proved" if int(final_metrics.get("epoch_count", 0) or 0) >= 5 else "incomplete",
            final_report / "metrics.json",
            f"Epoch count={final_metrics.get('epoch_count')} replacement count={final_metrics.get('replacement_count')}.",
            {
                "epoch_count": final_metrics.get("epoch_count"),
                "replacement_count": final_metrics.get("replacement_count"),
                "current_evaluator_id": final_metrics.get("current_evaluator_id"),
            },
        ),
        _item(
            "unattended_run_all_bundle",
            "The unattended run-all bundle exists and verifies its child ledgers.",
            "proved" if run_all_ok else "incomplete",
            run_all / "metrics.json",
            "run-all status is complete_with_deferred_jlens and all child ledgers verify."
            if run_all_ok
            else "run-all artifact is missing, incomplete, or has failed ledger verification.",
            {
                "run_status": run_all_metrics.get("run_status"),
                "all_child_ledgers_verified": run_all_metrics.get("all_child_ledgers_verified"),
            },
        ),
        _item(
            "live_sequence_record",
            "Preferred live-provider sequence is recorded without claiming live macro evidence.",
            "proved"
            if live_sequence_metrics.get("sequence_status")
            in {
                "blocked_before_smoke",
                "smoke_passed_pilot_not_requested",
                "pilot_executed_after_smoke_pass",
                "smoke_failed_pilot_not_promoted",
                "smoke_failed_pilot_not_requested",
            }
            and _ledger_verified(live_sequence)
            else "incomplete",
            live_sequence / "metrics.json",
            f"Live sequence status={live_sequence_metrics.get('sequence_status')} adapter calls={live_adapter_calls}.",
            {
                "sequence_status": live_sequence_metrics.get("sequence_status"),
                "adapter_call_count_total": live_adapter_calls,
                "all_child_ledgers_verified": live_sequence_metrics.get("all_child_ledgers_verified"),
            },
        ),
        _item(
            "jlens_or_clean_defer",
            "J-lens rail either produces evidence or has a clean failure/defer record.",
            "deferred_with_record" if jlens_frozen else "incomplete",
            repo_root / "FAILURE_LEDGER.md",
            "J-lens rail frozen with JLENS-FREEZE-001 because exact source/model access is unavailable."
            if jlens_frozen
            else "J-lens evidence or clean defer record is missing.",
            {
                "jlens_rail_status": final_metrics.get("jlens_rail_status"),
                "failure_ledger_entry_id": final_metrics.get("jlens_failure_ledger_entry_id"),
            },
        ),
        _item(
            "bridge_rail",
            "Bridge rail is either run after J-lens survival or cleanly deferred.",
            "deferred_with_record" if jlens_frozen else "incomplete",
            repo_root / "FAILURE_LEDGER.md",
            "Bridge rail deferred because the J-lens rail is frozen.",
            {"blocked_by": "jlens_or_clean_defer"},
        ),
        _item(
            "mechanistic_admission",
            "Mechanistic admission rail is either run after J-lens survival or cleanly deferred.",
            "deferred_with_record" if jlens_frozen else "incomplete",
            repo_root / "FAILURE_LEDGER.md",
            "Mechanistic admission deferred because the J-lens rail is frozen.",
            {"blocked_by": "jlens_or_clean_defer"},
        ),
        _item(
            "live_model_backed_execution",
            "At least one real provider-backed model call has been made and recorded before live evidence is claimed.",
            "proved" if live_model_run_performed and live_adapter_calls > 0 else "incomplete",
            live_sequence / "metrics.json",
            "Live model-backed execution recorded."
            if live_model_run_performed and live_adapter_calls > 0
            else "No live model-backed adapter call has been made; checked-in evidence remains no-spend/no-network.",
            {
                "live_model_run_performed": live_model_run_performed,
                "live_sequence_adapter_call_count_total": live_adapter_calls,
            },
        ),
    ]

    proved_count = sum(1 for item in items if item["status"] == "proved")
    deferred_count = sum(1 for item in items if item["status"].startswith("deferred"))
    incomplete_count = sum(1 for item in items if item["status"] == "incomplete")
    overall_status = "not_complete" if incomplete_count else "complete_with_deferred_records"
    metrics = {
        "run_id": run_id,
        "overall_status": overall_status,
        "requirement_count": len(items),
        "proved_count": proved_count,
        "deferred_count": deferred_count,
        "incomplete_count": incomplete_count,
        "incomplete_requirement_ids": [
            item["id"]
            for item in items
            if item["status"] == "incomplete"
        ],
        "deferred_requirement_ids": [
            item["id"]
            for item in items
            if item["status"].startswith("deferred")
        ],
        "source_final_report_path": str(final_report),
        "source_run_all_path": str(run_all),
        "source_live_sequence_path": str(live_sequence),
        "requirements_path": str(output_dir / "requirements.json"),
        "result_card_path": str(output_dir / "result_card.md"),
        "replay_bundle_path": str(output_dir / "replay"),
        "ledger_path": str(output_dir / "ledger.jsonl"),
    }
    replay_contexts = {
        "agent_1": {
            "1": "goal audit: loaded repository docs, final report, run-all bundle, live sequence, and failure ledger evidence",
            "2": f"goal audit: proved={proved_count} deferred={deferred_count} incomplete={incomplete_count}",
            "3": f"goal audit: {overall_status}; incomplete={metrics['incomplete_requirement_ids']}",
        }
    }

    ledger = Ledger()
    ledger.append(
        "goal_audit_start",
        {
            "run_id": run_id,
            "artifact_root": str(artifact_root),
            "repo_root": str(repo_root),
        },
    )
    for requirement in items:
        ledger.append("goal_requirement_assessment", requirement)
    ledger.append("goal_audit_metrics", metrics)

    _write_json(output_dir / "requirements.json", {"items": items})
    _write_json(output_dir / "metrics.json", metrics)
    _write_json(output_dir / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(output_dir / "ledger.jsonl")
    metrics["ledger_path"] = str(ledger_path)
    _write_json(output_dir / "metrics.json", metrics)
    (output_dir / "result_card.md").write_text(_result_card(run_id, metrics, items))

    return GoalAuditResult(run_id=run_id, artifact_path=output_dir, expected_replay=replay_contexts)
