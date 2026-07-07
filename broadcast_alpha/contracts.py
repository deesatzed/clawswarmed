from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Candidate:
    id: str
    score: float
    slot_type: str
    agent_id: str = "agent_0"
    task_id: str = "task_0"
    run_id: str = "run_0"
    seed_status: str = "organic"
    payload_text: str = ""
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Slot:
    slot_type: str
    candidate_id: str
    admitted_by: str
    epoch_id: str
    ttl: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Evaluator:
    id: str
    kind: str
    status: str = "active"
    model_ref: str = "scripted"
    lineage_parent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Epoch:
    id: str
    active_evaluator: str
    status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Task:
    id: str
    suite: str
    verifier: str
    seed_condition: str = "none"
    panel_type: str = "partitioned_disjoint_shards"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetricsRecord:
    run_id: str
    prereg_id: str
    glassgate_lift: float
    glassgate_lift_ci95: list[float]
    D_by_arm: dict[str, float] = field(default_factory=dict)
    D_by_panel_type: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
