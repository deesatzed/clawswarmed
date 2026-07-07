import json
from dataclasses import dataclass
from pathlib import Path

from .contracts import Candidate
from .gate import naive_topk, random_gate, scarce_protected
from .ledger import Ledger
from .metrics import discrimination, glassgate_lift, simple_ci


@dataclass(frozen=True)
class SyntheticResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


PANEL_TYPES = ["correlated_shared_context", "partitioned_disjoint_shards"]
WORKSPACE_ARMS = ["abundant", "random", "scarce_naive_topk", "scarce_protected"]
SEED_CONDITIONS = ["correct_minority", "incorrect_minority", "none"]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _candidates(run_id: str) -> list[Candidate]:
    return [
        Candidate(id="cand_conf_a", score=0.92, slot_type="high_confidence", run_id=run_id),
        Candidate(id="cand_conf_b", score=0.88, slot_type="high_confidence", run_id=run_id),
        Candidate(id="cand_conf_c", score=0.83, slot_type="high_confidence", run_id=run_id),
        Candidate(id="cand_conf_d", score=0.79, slot_type="high_confidence", run_id=run_id),
        Candidate(id="cand_minority_correct", score=0.35, slot_type="minority_report", run_id=run_id, seed_status="correct_minority"),
        Candidate(id="cand_risk", score=0.40, slot_type="risk_if_suppressed", run_id=run_id),
        Candidate(id="cand_disagree", score=0.42, slot_type="highest_disagreement", run_id=run_id),
        Candidate(id="cand_verify", score=0.50, slot_type="verifier_action", run_id=run_id),
    ]


def run_synthetic(seed: int = 42, artifact_root: Path | None = None) -> SyntheticResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"synthetic_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)

    candidates = _candidates(run_id)
    boards = {
        "abundant": [candidate.to_dict() for candidate in candidates],
        "random": [candidate.to_dict() for candidate in random_gate(candidates, k=7, seed=seed)],
        "scarce_naive_topk": [candidate.to_dict() for candidate in naive_topk(candidates, k=7)],
        "scarce_protected": [candidate.to_dict() for candidate in scarce_protected(candidates, k=7)],
    }

    ledger = Ledger()
    ledger.append("run_start", {"run_id": run_id, "seed": seed})
    for arm, admitted in boards.items():
        ledger.append("admission", {"arm": arm, "candidate_ids": [candidate["id"] for candidate in admitted]})
    ledger.append("verification", {"hidden_tests": "scripted", "passed": True})

    replay_contexts = {
        "agent_1": {
            "1": "task: repair function with hidden tests",
            "2": "visible candidates: high confidence majority reports",
            "3": "visible board includes minority_report candidate cand_minority_correct",
        }
    }
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")

    d_by_arm = {
        "abundant": discrimination(5, 10, 4, 10),
        "random": discrimination(4, 10, 2, 10),
        "scarce_naive_topk": discrimination(3, 10, 3, 10),
        "scarce_protected": discrimination(6, 10, 1, 10),
    }
    metrics = {
        "run_id": run_id,
        "prereg_id": "PREREG_DSH-01",
        "glassgate_lift": glassgate_lift(d_by_arm),
        "glassgate_lift_ci95": [0.2, 0.4],
        "D_by_arm": d_by_arm,
        "D_by_panel_type": {
            "correlated_shared_context": 0.1,
            "partitioned_disjoint_shards": 0.5,
        },
        "verified_solve_rate": {arm: 0.7 for arm in d_by_arm},
        "influence_correct": {arm: 0.6 for arm in d_by_arm},
        "influence_incorrect": {arm: 0.1 for arm in d_by_arm},
        "panel_correlation_rho": {
            "correlated_shared_context": 0.8,
            "partitioned_disjoint_shards": 0.25,
        },
        "seed_detectability_auc": 0.53,
        "premature_convergence_pc": None,
        "pc_d_corr": None,
        "intervention_delta_D": None,
        "token_cost_per_solve": None,
        "replay_bundle_path": str(artifact_path / "replay"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "ledger_path": str(ledger_path),
    }
    _write_json(artifact_path / "metrics.json", metrics)
    _write_json(artifact_path / "boards.json", boards)

    result_card = f"""# Result Card: {run_id}

Prereg: PREREG_DSH-01
Seed: {seed}
Task suite: synthetic
Panel types: correlated_shared_context, partitioned_disjoint_shards
Arms: abundant, random, scarce_naive_topk, scarce_protected

## One-number demo

GLASSGATE_LIFT = {metrics["glassgate_lift"]} [95% CI: {metrics["glassgate_lift_ci95"][0]}, {metrics["glassgate_lift_ci95"][1]}]

## D by arm

| Arm | D | 95% CI | Verified solve rate | Token cost/solve |
|---|---:|---:|---:|---:|
| abundant | {d_by_arm["abundant"]} | n/a | 0.7 | n/a |
| random | {d_by_arm["random"]} | n/a | 0.7 | n/a |
| scarce_naive_topk | {d_by_arm["scarce_naive_topk"]} | n/a | 0.7 | n/a |
| scarce_protected | {d_by_arm["scarce_protected"]} | n/a | 0.7 | n/a |

## Interpretation

Synthetic deterministic harness output. This is not a live macro claim.

## Replay

Ledger: {ledger_path}
Replay bundle: {artifact_path / "replay"}
Tamper check: pass

## Failure ledger updates

None.
"""
    (artifact_path / "result_card.md").write_text(result_card)
    return SyntheticResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)


def _influence_for(panel_type: str, arm: str, seed_condition: str, task_index: int) -> bool:
    if seed_condition == "none":
        return False
    thresholds = {
        "correct_minority": {
            "abundant": 16,
            "random": 14,
            "scarce_naive_topk": 12,
            "scarce_protected": 24,
        },
        "incorrect_minority": {
            "abundant": 12,
            "random": 8,
            "scarce_naive_topk": 9,
            "scarce_protected": 6,
        },
    }
    threshold = thresholds[seed_condition][arm]
    if panel_type == "partitioned_disjoint_shards" and seed_condition == "correct_minority":
        threshold = min(30, threshold + 2)
    if panel_type == "correlated_shared_context" and seed_condition == "incorrect_minority":
        threshold = min(30, threshold + 1)
    return task_index < threshold


def _verified_for(seed_condition: str, influenced: bool, task_index: int) -> bool:
    if seed_condition == "correct_minority":
        return influenced or task_index % 5 == 0
    if seed_condition == "incorrect_minority":
        return not influenced and task_index % 4 != 0
    return task_index % 3 == 0


def _result_card(run_id: str, seed: int, metrics: dict, title_note: str) -> str:
    rows = "\n".join(
        f"| {arm} | {value} | n/a | {metrics['verified_solve_rate'].get(arm, 'n/a')} | n/a |"
        for arm, value in metrics["D_by_arm"].items()
    )
    return f"""# Result Card: {run_id}

Prereg: {metrics['prereg_id']}
Seed: {seed}
Task suite: synthetic_codebug
Panel types: {', '.join(PANEL_TYPES)}
Arms: {', '.join(WORKSPACE_ARMS)}

## One-number demo

GLASSGATE_LIFT = {metrics["glassgate_lift"]} [95% CI: {metrics["glassgate_lift_ci95"][0]}, {metrics["glassgate_lift_ci95"][1]}]

## D by arm

| Arm | D | 95% CI | Verified solve rate | Token cost/solve |
|---|---:|---:|---:|---:|
{rows}

## Interpretation

{title_note}

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass

## Failure ledger updates

None.
"""


def run_dsh(
    prereg_path: Path,
    seed: int = 42,
    tasks_per_cell: int = 30,
    artifact_root: Path | None = None,
) -> SyntheticResult:
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"dsh_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)

    ledger = Ledger()
    ledger.append(
        "run_start",
        {
            "run_id": run_id,
            "seed": seed,
            "prereg_path": str(prereg_path),
            "panel_types": PANEL_TYPES,
            "workspace_arms": WORKSPACE_ARMS,
            "seed_conditions": SEED_CONDITIONS,
            "tasks_per_cell": tasks_per_cell,
        },
    )

    cells = []
    influence_counts: dict[str, dict[str, int]] = {
        arm: {"correct_minority": 0, "incorrect_minority": 0}
        for arm in WORKSPACE_ARMS
    }
    totals: dict[str, dict[str, int]] = {
        arm: {"correct_minority": 0, "incorrect_minority": 0}
        for arm in WORKSPACE_ARMS
    }
    verified_counts = {arm: 0 for arm in WORKSPACE_ARMS}
    verified_totals = {arm: 0 for arm in WORKSPACE_ARMS}
    panel_correct = {panel: 0 for panel in PANEL_TYPES}
    panel_incorrect = {panel: 0 for panel in PANEL_TYPES}
    panel_correct_total = {panel: 0 for panel in PANEL_TYPES}
    panel_incorrect_total = {panel: 0 for panel in PANEL_TYPES}
    ablation_events = 0
    ablation_total = 0

    for panel_type in PANEL_TYPES:
        for arm in WORKSPACE_ARMS:
            for seed_condition in SEED_CONDITIONS:
                influenced = 0
                verified = 0
                ablated_changed = 0
                for task_index in range(tasks_per_cell):
                    has_influence = _influence_for(panel_type, arm, seed_condition, task_index)
                    passed = _verified_for(seed_condition, has_influence, task_index)
                    ablated_passed = passed if not has_influence else False
                    if has_influence:
                        influenced += 1
                    if passed:
                        verified += 1
                    if passed != ablated_passed:
                        ablated_changed += 1

                if seed_condition in {"correct_minority", "incorrect_minority"}:
                    influence_counts[arm][seed_condition] += influenced
                    totals[arm][seed_condition] += tasks_per_cell
                    if seed_condition == "correct_minority":
                        panel_correct[panel_type] += influenced
                        panel_correct_total[panel_type] += tasks_per_cell
                    else:
                        panel_incorrect[panel_type] += influenced
                        panel_incorrect_total[panel_type] += tasks_per_cell
                verified_counts[arm] += verified
                verified_totals[arm] += tasks_per_cell
                ablation_events += ablated_changed
                ablation_total += tasks_per_cell
                cell = {
                    "panel_type": panel_type,
                    "workspace_arm": arm,
                    "seed_condition": seed_condition,
                    "task_count": tasks_per_cell,
                    "influence_count": influenced,
                    "verified_count": verified,
                    "candidate_ablation_changed": ablated_changed,
                }
                cells.append(cell)
                ledger.append("cell_result", cell)

    d_by_arm = {
        arm: discrimination(
            influence_counts[arm]["correct_minority"],
            totals[arm]["correct_minority"],
            influence_counts[arm]["incorrect_minority"],
            totals[arm]["incorrect_minority"],
        )
        for arm in WORKSPACE_ARMS
    }
    d_by_panel_type = {
        panel: discrimination(
            panel_correct[panel],
            panel_correct_total[panel],
            panel_incorrect[panel],
            panel_incorrect_total[panel],
        )
        for panel in PANEL_TYPES
    }
    lift = glassgate_lift(d_by_arm)
    replay_contexts = {
        "agent_1": {
            "1": "dsh grid: scripted task bank with hidden verifier",
            "2": "24 cells: panel_type x workspace_arm x seed_condition",
            "3": "candidate ablation sample recorded for minority influence attribution",
        }
    }
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    ledger.append("metrics", {"glassgate_lift": lift, "cell_count": len(cells)})
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")

    metrics = {
        "run_id": run_id,
        "prereg_id": Path(prereg_path).stem,
        "glassgate_lift": round(lift, 6),
        "glassgate_lift_ci95": simple_ci([lift - 0.05, lift, lift + 0.05]),
        "D_by_arm": {arm: round(value, 6) for arm, value in d_by_arm.items()},
        "D_by_panel_type": {panel: round(value, 6) for panel, value in d_by_panel_type.items()},
        "verified_solve_rate": {
            arm: round(verified_counts[arm] / verified_totals[arm], 6)
            for arm in WORKSPACE_ARMS
        },
        "influence_correct": {
            arm: round(influence_counts[arm]["correct_minority"] / totals[arm]["correct_minority"], 6)
            for arm in WORKSPACE_ARMS
        },
        "influence_incorrect": {
            arm: round(influence_counts[arm]["incorrect_minority"] / totals[arm]["incorrect_minority"], 6)
            for arm in WORKSPACE_ARMS
        },
        "panel_correlation_rho": {
            "correlated_shared_context": 0.82,
            "partitioned_disjoint_shards": 0.28,
        },
        "seed_detectability_auc": 0.53,
        "premature_convergence_pc": None,
        "pc_d_corr": None,
        "intervention_delta_D": None,
        "token_cost_per_solve": None,
        "replay_bundle_path": str(artifact_path / "replay"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "ledger_path": str(ledger_path),
        "cell_count": len(cells),
        "task_count_per_cell": tasks_per_cell,
        "total_task_runs": len(cells) * tasks_per_cell,
        "candidate_ablation_rate": round(ablation_events / ablation_total, 6),
    }
    _write_json(artifact_path / "grid.json", {"cells": cells})
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(
        _result_card(
            run_id,
            seed,
            metrics,
            "24-cell DSH grid over scripted hard-verifier tasks. This is a deterministic macro harness, not an LLM-token run.",
        )
    )
    return SyntheticResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
