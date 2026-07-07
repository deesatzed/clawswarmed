class EpochAuthority:
    def __init__(self, active_evaluator: str) -> None:
        self.active_evaluator = active_evaluator
        self.history: list[dict] = []

    def add_score(self, score_id: str, evaluator_id: str, value: float, status: str = "active") -> None:
        self.history.append(
            {
                "id": score_id,
                "evaluator_id": evaluator_id,
                "value": value,
                "status": status,
            }
        )

    def tombstone_evaluator(self, evaluator_id: str, reason: str) -> None:
        for score in self.history:
            if score["evaluator_id"] == evaluator_id:
                score["status"] = "tombstoned"
                score["tombstone_reason"] = reason

    def current_scores(self) -> list[dict]:
        return [score for score in self.history if score["status"] == "active"]

    def to_dict(self) -> dict:
        return {
            "active_evaluator": self.active_evaluator,
            "history": self.history,
            "current_scores": self.current_scores(),
        }
