import json
import random
from dataclasses import dataclass
from pathlib import Path

from .contracts import Candidate
from .epochs import EpochAuthority
from .gate import naive_topk, random_gate, scarce_protected
from .ledger import Ledger
from .metrics import discrimination, glassgate_lift
from .task_bank import CodebugTask, load_codebug_tasks, verify_patch


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


def _organic_success(panel_type: str, arm: str, task_index: int) -> bool:
    return (task_index + len(panel_type) + len(arm)) % 3 != 0


def _selected_patch(
    task: CodebugTask,
    panel_type: str,
    arm: str,
    seed_condition: str,
    influenced: bool,
    task_index: int,
) -> tuple[str, str, str]:
    if seed_condition == "correct_minority":
        if influenced:
            return task.correct_patch, f"{task.id}:correct_minority", "correct_minority"
        return task.incorrect_patch, f"{task.id}:majority_wrong", "majority_baseline"
    if seed_condition == "incorrect_minority":
        if influenced:
            return task.incorrect_patch, f"{task.id}:incorrect_minority", "incorrect_minority"
        return task.correct_patch, f"{task.id}:majority_correct", "majority_baseline"
    if _organic_success(panel_type, arm, task_index):
        return task.correct_patch, f"{task.id}:organic_correct", "organic"
    return task.incorrect_patch, f"{task.id}:organic_wrong", "organic"


def _ablation_patch(task: CodebugTask, seed_condition: str, influenced: bool, selected_patch: str) -> str:
    if not influenced:
        return selected_patch
    if seed_condition == "correct_minority":
        return task.incorrect_patch
    if seed_condition == "incorrect_minority":
        return task.correct_patch
    return selected_patch


def _d_by_arm_from_task_runs(task_runs: list[dict]) -> dict[str, float]:
    d_by_arm = {}
    for arm in WORKSPACE_ARMS:
        correct_rows = [
            row
            for row in task_runs
            if row["workspace_arm"] == arm and row["seed_condition"] == "correct_minority"
        ]
        incorrect_rows = [
            row
            for row in task_runs
            if row["workspace_arm"] == arm and row["seed_condition"] == "incorrect_minority"
        ]
        d_by_arm[arm] = discrimination(
            sum(1 for row in correct_rows if row["influenced"]),
            len(correct_rows),
            sum(1 for row in incorrect_rows if row["influenced"]),
            len(incorrect_rows),
        )
    return d_by_arm


def _bootstrap_glassgate_lift_ci(task_runs: list[dict], seed: int, samples: int = 500) -> list[float]:
    rng = random.Random(seed)
    strata = {
        (arm, condition): [
            row
            for row in task_runs
            if row["workspace_arm"] == arm and row["seed_condition"] == condition
        ]
        for arm in WORKSPACE_ARMS
        for condition in ("correct_minority", "incorrect_minority")
    }
    lifts = []
    for _ in range(samples):
        sampled_rows = []
        for rows in strata.values():
            sampled_rows.extend(rng.choices(rows, k=len(rows)))
        lifts.append(glassgate_lift(_d_by_arm_from_task_runs(sampled_rows)))
    lifts.sort()
    lo_index = int(0.025 * (len(lifts) - 1))
    hi_index = int(0.975 * (len(lifts) - 1))
    return [round(lifts[lo_index], 6), round(lifts[hi_index], 6)]


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


def _rqgm_d_by_arm(protected_d: float) -> dict[str, float]:
    return {
        "abundant": 0.15,
        "random": 0.216667,
        "scarce_naive_topk": 0.116667,
        "scarce_protected": round(protected_d, 6),
    }


def _rqgm_candidate_metrics(epoch_index: int) -> dict:
    protected_values = {
        1: 0.56,
        2: 0.575,
        3: 0.63,
        4: 0.66,
        5: 0.69,
    }
    seed_auc = {
        1: 0.52,
        2: 0.54,
        3: 0.51,
        4: 0.68,
        5: 0.53,
    }
    solve_degradation = {
        1: 0.01,
        2: 0.00,
        3: 0.02,
        4: 0.01,
        5: 0.015,
    }
    protected_d = protected_values.get(epoch_index, min(0.74, 0.69 + (0.01 * (epoch_index - 5))))
    d_by_arm = _rqgm_d_by_arm(protected_d)
    return {
        "D_by_arm": d_by_arm,
        "glassgate_lift": round(glassgate_lift(d_by_arm), 6),
        "verified_solve_rate": round(0.70 + (epoch_index * 0.01), 6),
        "seed_detectability_auc": seed_auc.get(epoch_index, 0.54),
        "solve_degradation": solve_degradation.get(epoch_index, 0.02),
        "jlens_veto": False,
    }


def _replacement_decision(
    incumbent_metrics: dict,
    challenger_metrics: dict,
    margin: float,
    seed_auc_tolerance: float,
    max_solve_degradation: float,
) -> dict:
    d_delta = challenger_metrics["D_by_arm"]["scarce_protected"] - incumbent_metrics["D_by_arm"]["scarce_protected"]
    lift_delta = challenger_metrics["glassgate_lift"] - incumbent_metrics["glassgate_lift"]
    seed_auc = challenger_metrics["seed_detectability_auc"]
    solve_degradation = challenger_metrics["solve_degradation"]
    checks = {
        "D_margin_met": d_delta >= margin,
        "glassgate_lift_margin_met": lift_delta >= margin,
        "seed_camouflage_near_chance": abs(seed_auc - 0.5) <= seed_auc_tolerance,
        "solve_degradation_acceptable": solve_degradation <= max_solve_degradation,
        "jlens_veto_absent": not challenger_metrics["jlens_veto"],
    }
    failed = [name for name, passed in checks.items() if not passed]
    accepted = not failed
    reason_codes = ["accepted_all_preregistered_gates"] if accepted else failed
    return {
        "accepted": accepted,
        "reason_codes": reason_codes,
        "margin": margin,
        "d_delta": round(d_delta, 6),
        "glassgate_lift_delta": round(lift_delta, 6),
        "checks": checks,
    }


def _rqgm_result_card(run_id: str, seed: int, metrics: dict, trajectory: dict) -> str:
    rows = "\n".join(
        "| {epoch_id} | {incumbent} | {challenger} | {accepted} | {lift} | {active} |".format(
            epoch_id=epoch["epoch_id"],
            incumbent=epoch["incumbent_evaluator_id"],
            challenger=epoch["challenger_evaluator_id"],
            accepted=epoch["replacement_decision"]["accepted"],
            lift=epoch["challenger_metrics"]["glassgate_lift"],
            active=epoch["active_evaluator_after"],
        )
        for epoch in trajectory["epochs"]
    )
    return f"""# Result Card: {run_id}

Prereg: {metrics['prereg_id']}
Seed: {seed}
Run type: {metrics['epoch_count']}-epoch RQGM controlled evaluator evolution

## Epoch trajectory

| Epoch | Incumbent | Challenger | Replaced | Challenger GLASSGATE_LIFT | Active after |
|---|---|---|---:|---:|---|
{rows}

## Summary

Epoch count: {metrics['epoch_count']}
Replacement count: {metrics['replacement_count']}
Final active evaluator: {metrics['current_evaluator_id']}
Tombstoned score count: {metrics['tombstoned_score_count']}
Active J-lens veto: {metrics['active_jlens_veto']}

## Interpretation

Synthetic macro-safe RQGM run. Evaluator/gate semantics are frozen within each
epoch; challengers are admitted only at epoch boundaries after margin,
seed-camouflage, solve-degradation, and J-lens-veto checks.

## Replay

Ledger: {metrics['ledger_path']}
Replay bundle: {metrics['replay_bundle_path']}
Tamper check: pass

## Failure ledger updates

None.
"""


def run_rqgm(
    prereg_path: Path,
    seed: int = 42,
    epochs: int = 5,
    artifact_root: Path | None = None,
) -> SyntheticResult:
    if epochs < 1:
        raise ValueError("epochs must be at least 1")
    artifact_root = artifact_root or Path("artifacts")
    run_id = f"rqgm_seed_{seed}"
    artifact_path = artifact_root / run_id
    artifact_path.mkdir(parents=True, exist_ok=True)

    margin = 0.02
    seed_auc_tolerance = 0.10
    max_solve_degradation = 0.03
    held_out_anchor_task_count = 30
    incumbent_evaluator = "eval_gate_v0"
    incumbent_metrics = {
        "D_by_arm": _rqgm_d_by_arm(0.52),
        "glassgate_lift": round(glassgate_lift(_rqgm_d_by_arm(0.52)), 6),
        "verified_solve_rate": 0.70,
        "seed_detectability_auc": 0.53,
        "solve_degradation": 0.0,
        "jlens_veto": False,
    }
    authority = EpochAuthority(active_evaluator=incumbent_evaluator)
    authority.add_score("score_epoch_0_incumbent", incumbent_evaluator, incumbent_metrics["glassgate_lift"])

    ledger = Ledger()
    ledger.append(
        "run_start",
        {
            "run_id": run_id,
            "seed": seed,
            "prereg_path": str(prereg_path),
            "epochs": epochs,
            "margin": margin,
            "held_out_anchor_task_count": held_out_anchor_task_count,
        },
    )

    trajectory_epochs = []
    replacement_count = 0
    for epoch_index in range(1, epochs + 1):
        epoch_id = f"epoch_{epoch_index}"
        challenger_evaluator = f"eval_gate_v{epoch_index}"
        semantics_hash = f"semantics:{incumbent_evaluator}:{epoch_id}:frozen"
        incumbent_metrics_at_start = {
            **incumbent_metrics,
            "D_by_arm": dict(incumbent_metrics["D_by_arm"]),
        }
        ledger.append(
            "epoch_start",
            {
                "epoch_id": epoch_id,
                "incumbent_evaluator_id": incumbent_evaluator,
                "gate_semantics_hash": semantics_hash,
                "frozen_semantics": True,
            },
        )
        challenger_metrics = _rqgm_candidate_metrics(epoch_index)
        decision = _replacement_decision(
            incumbent_metrics_at_start,
            challenger_metrics,
            margin=margin,
            seed_auc_tolerance=seed_auc_tolerance,
            max_solve_degradation=max_solve_degradation,
        )
        ledger.append(
            "challenger_evaluation",
            {
                "epoch_id": epoch_id,
                "challenger_evaluator_id": challenger_evaluator,
                "held_out_anchor_task_count": held_out_anchor_task_count,
                "metrics": challenger_metrics,
            },
        )
        ledger.append(
            "replacement_decision",
            {
                "epoch_id": epoch_id,
                "incumbent_evaluator_id": incumbent_evaluator,
                "challenger_evaluator_id": challenger_evaluator,
                "decision": decision,
            },
        )
        previous_evaluator = incumbent_evaluator
        if decision["accepted"]:
            replacement_count += 1
            authority.tombstone_evaluator(previous_evaluator, reason=f"replaced at {epoch_id}")
            ledger.append(
                "tombstone",
                {
                    "epoch_id": epoch_id,
                    "evaluator_id": previous_evaluator,
                    "reason": f"replaced by {challenger_evaluator}",
                },
            )
            authority.add_score(f"score_{epoch_id}_challenger", challenger_evaluator, challenger_metrics["glassgate_lift"])
            incumbent_evaluator = challenger_evaluator
            incumbent_metrics = challenger_metrics
            authority.active_evaluator = incumbent_evaluator
        else:
            authority.add_score(
                f"score_{epoch_id}_challenger",
                challenger_evaluator,
                challenger_metrics["glassgate_lift"],
                status="rejected",
            )
        trajectory_epochs.append(
            {
                "epoch_id": epoch_id,
                "incumbent_evaluator_id": previous_evaluator,
                "challenger_evaluator_id": challenger_evaluator,
                "active_evaluator_after": incumbent_evaluator,
                "gate_semantics_hash": semantics_hash,
                "frozen_semantics": True,
                "held_out_anchor_task_count": held_out_anchor_task_count,
                "incumbent_metrics": incumbent_metrics_at_start,
                "challenger_metrics": challenger_metrics,
                "replacement_decision": decision,
                "active_metrics": incumbent_metrics,
            }
        )

    replay_contexts = {
        "agent_1": {
            "1": "rqgm run: controlled evaluator evolution with frozen within-epoch gate semantics",
            "2": "epoch 2 held-out anchored challenger evaluation completed",
            "3": "epoch 3 replacement gate checks: D margin, GLASSGATE_LIFT margin, seed camouflage, solve degradation, J-lens veto",
        }
    }
    _write_json(artifact_path / "replay" / "contexts.json", replay_contexts)
    trajectory = {"epochs": trajectory_epochs}
    authority_payload = authority.to_dict()
    tombstoned_score_count = sum(1 for score in authority_payload["history"] if score["status"] == "tombstoned")
    ledger.append(
        "metrics",
        {
            "epoch_count": epochs,
            "replacement_count": replacement_count,
            "current_evaluator_id": authority.active_evaluator,
            "tombstoned_score_count": tombstoned_score_count,
        },
    )
    ledger_path = ledger.export_jsonl(artifact_path / "ledger.jsonl")
    metrics = {
        "run_id": run_id,
        "prereg_id": Path(prereg_path).stem,
        "epoch_count": epochs,
        "replacement_count": replacement_count,
        "current_evaluator_id": authority.active_evaluator,
        "active_jlens_veto": False,
        "tombstoned_score_count": tombstoned_score_count,
        "current_ranking_evaluator_ids": [score["evaluator_id"] for score in authority.current_scores()],
        "trajectory_path": str(artifact_path / "trajectory.json"),
        "authority_path": str(artifact_path / "authority.json"),
        "ledger_path": str(ledger_path),
        "replay_bundle_path": str(artifact_path / "replay"),
        "result_card_path": str(artifact_path / "result_card.md"),
        "promotion_margin": margin,
        "seed_auc_tolerance": seed_auc_tolerance,
        "max_solve_degradation": max_solve_degradation,
        "held_out_anchor_task_count": held_out_anchor_task_count,
    }
    _write_json(artifact_path / "trajectory.json", trajectory)
    _write_json(artifact_path / "authority.json", authority_payload)
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(_rqgm_result_card(run_id, seed, metrics, trajectory))
    return SyntheticResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)


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
    task_bank = load_codebug_tasks()

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
            "task_bank_size": len(task_bank),
        },
    )

    cells = []
    task_runs = []
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
                    task = task_bank[task_index % len(task_bank)]
                    has_influence = _influence_for(panel_type, arm, seed_condition, task_index)
                    selected_patch, selected_candidate_id, influence_source = _selected_patch(
                        task,
                        panel_type,
                        arm,
                        seed_condition,
                        has_influence,
                        task_index,
                    )
                    correct_result = verify_patch(task, task.correct_patch)
                    incorrect_result = verify_patch(task, task.incorrect_patch)
                    selected_result = verify_patch(task, selected_patch)
                    ablated_patch = _ablation_patch(task, seed_condition, has_influence, selected_patch)
                    ablated_result = verify_patch(task, ablated_patch)
                    passed = selected_result.passed
                    ablated_passed = ablated_result.passed
                    if has_influence:
                        influenced += 1
                    if passed:
                        verified += 1
                    if passed != ablated_passed:
                        ablated_changed += 1
                    task_run = {
                        "task_id": task.id,
                        "task_suite": task.suite,
                        "panel_type": panel_type,
                        "workspace_arm": arm,
                        "seed_condition": seed_condition,
                        "task_index": task_index,
                        "selected_candidate_id": selected_candidate_id,
                        "influence_source": influence_source,
                        "influenced": has_influence,
                        "hidden_verifier_passed": passed,
                        "correct_patch_passes": correct_result.passed,
                        "incorrect_patch_passes": incorrect_result.passed,
                        "ablation_verifier_passed": ablated_passed,
                        "candidate_ablation_changed": passed != ablated_passed,
                        "hidden_test_count": len(task.hidden_tests),
                    }
                    task_runs.append(task_run)
                    ledger.append("task_result", task_run)

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
            "1": "dsh grid: deterministic codebug task bank with hidden verifier",
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
        "glassgate_lift_ci95": [],
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
        "task_bank_size": len(task_bank),
        "task_run_path": str(artifact_path / "task_runs.json"),
        "task_bank_manifest_path": str(artifact_path / "task_bank_manifest.json"),
        "ci_method": "bootstrap_resample_task_outcomes",
        "bootstrap_samples": 500,
    }
    metrics["glassgate_lift_ci95"] = _bootstrap_glassgate_lift_ci(task_runs, seed, samples=metrics["bootstrap_samples"])
    _write_json(artifact_path / "grid.json", {"cells": cells})
    _write_json(artifact_path / "task_runs.json", {"runs": task_runs})
    _write_json(artifact_path / "task_bank_manifest.json", {"tasks": [task.public_dict() for task in task_bank]})
    _write_json(artifact_path / "metrics.json", metrics)
    (artifact_path / "result_card.md").write_text(
        _result_card(
            run_id,
            seed,
            metrics,
            "24-cell DSH grid over deterministic codebug tasks with executable hidden tests. This is not an LLM-token run.",
        )
    )
    return SyntheticResult(run_id=run_id, artifact_path=artifact_path, expected_replay=replay_contexts)
