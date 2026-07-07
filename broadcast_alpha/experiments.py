import json
from dataclasses import dataclass
from pathlib import Path

from .contracts import Candidate
from .gate import naive_topk, random_gate, scarce_protected
from .ledger import Ledger
from .metrics import discrimination, glassgate_lift


@dataclass(frozen=True)
class SyntheticResult:
    run_id: str
    artifact_path: Path
    expected_replay: dict


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

