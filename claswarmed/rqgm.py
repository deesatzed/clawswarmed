from dataclasses import dataclass


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

