import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import time_ns


@dataclass(frozen=True)
class EvaluatorSlot:
    name: str
    incumbent: str
    score: float


@dataclass(frozen=True)
class ReplacementDecision:
    slot: str
    active_evaluator: str
    replaced: bool
    rationale: str


@dataclass(frozen=True)
class ChallengerScore:
    name: str
    score: float
    anchor: str


@dataclass(frozen=True)
class EpochState:
    epoch_id: int
    slot: EvaluatorSlot
    utility_records: list[dict]
    lineage: list[dict]


def consider_replacement(
    slot: EvaluatorSlot,
    challenger: str,
    challenger_score: float,
    margin: float = 0.05,
) -> ReplacementDecision:
    improvement = challenger_score - slot.score
    if improvement >= margin:
        return ReplacementDecision(
            slot=slot.name,
            active_evaluator=challenger,
            replaced=True,
            rationale=(
                f"At the epoch boundary, challenger {challenger} beat "
                f"{slot.incumbent} by {improvement:.3f}, meeting margin {margin:.3f}."
            ),
        )

    return ReplacementDecision(
        slot=slot.name,
        active_evaluator=slot.incumbent,
        replaced=False,
        rationale=(
            f"Challenger {challenger} improved by {improvement:.3f}, below margin "
            f"{margin:.3f}; keep incumbent until a stronger epoch boundary candidate appears."
        ),
    )


def advance_epoch(
    state: EpochState,
    challengers: list[ChallengerScore],
    margin: float = 0.05,
) -> EpochState:
    if not challengers:
        event = {
            "from_epoch": state.epoch_id,
            "to_epoch": state.epoch_id + 1,
            "active_evaluator": state.slot.incumbent,
            "replaced": False,
            "erased_records": [],
            "note": "No challenger evaluators were available; evaluator snapshot remains frozen.",
        }
        return EpochState(
            epoch_id=state.epoch_id + 1,
            slot=state.slot,
            utility_records=list(state.utility_records),
            lineage=[*state.lineage, event],
        )

    best = max(challengers, key=lambda challenger: challenger.score)
    decision = consider_replacement(
        state.slot,
        challenger=best.name,
        challenger_score=best.score,
        margin=margin,
    )
    if not decision.replaced:
        event = {
            "from_epoch": state.epoch_id,
            "to_epoch": state.epoch_id + 1,
            "active_evaluator": state.slot.incumbent,
            "challenger": best.name,
            "anchor": best.anchor,
            "replaced": False,
            "erased_records": [],
            "note": "No evaluator replacement; challenger did not clear the epoch boundary margin.",
        }
        return EpochState(
            epoch_id=state.epoch_id + 1,
            slot=state.slot,
            utility_records=list(state.utility_records),
            lineage=[*state.lineage, event],
        )

    erased = [
        record["id"]
        for record in state.utility_records
        if record.get("evaluator") == state.slot.incumbent
    ]
    retained = [
        record
        for record in state.utility_records
        if record.get("evaluator") != state.slot.incumbent
    ]
    event = {
        "from_epoch": state.epoch_id,
        "to_epoch": state.epoch_id + 1,
        "active_evaluator": best.name,
        "challenger": best.name,
        "anchor": best.anchor,
        "replaced": True,
        "erased_records": erased,
        "note": (
            "Applied selective erasure for records scored by the displaced "
            f"evaluator {state.slot.incumbent}."
        ),
    }
    return EpochState(
        epoch_id=state.epoch_id + 1,
        slot=EvaluatorSlot(name=state.slot.name, incumbent=best.name, score=best.score),
        utility_records=retained,
        lineage=[*state.lineage, event],
    )


def epoch_to_dict(state: EpochState) -> dict:
    return asdict(state)


def demo_epoch_transition() -> EpochState:
    state = EpochState(
        epoch_id=1,
        slot=EvaluatorSlot(name="code-review", incumbent="claude-reviewer", score=0.72),
        utility_records=[
            {"id": "code-review-001", "evaluator": "claude-reviewer", "score": 0.72},
            {"id": "rubric-anchor-001", "evaluator": "rubric-anchor", "score": 0.90},
        ],
        lineage=[],
    )
    return advance_epoch(
        state,
        challengers=[
            ChallengerScore(name="grok-reviewer", score=0.73, anchor="held-out coding tasks"),
            ChallengerScore(name="gemini-reviewer", score=0.80, anchor="held-out coding tasks"),
        ],
    )


def save_lineage(app_root: Path, state: EpochState) -> str:
    state_dir = app_root / ".claswarmed" / "lineage"
    state_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = state_dir / f"{timestamp}-{time_ns()}-epoch-{state.epoch_id}.json"
    path.write_text(json.dumps(epoch_to_dict(state), indent=2, sort_keys=True) + "\n")
    return str(path)


def load_lineage(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())
