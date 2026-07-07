class EpochAuthority:
    def __init__(self, active_evaluator: str) -> None:
        self.active_evaluator = active_evaluator
        self.history: list[dict] = []

    def add_score(self, score_id: str, evaluator_id: str, value: float) -> None:
        self.history.append(
            {
                "id": score_id,
                "evaluator_id": evaluator_id,
                "value": value,
                "status": "active",
            }
        )

    def tombstone_evaluator(self, evaluator_id: str, reason: str) -> None:
        for score in self.history:
            if score["evaluator_id"] == evaluator_id:
                score["status"] = "tombstoned"
                score["tombstone_reason"] = reason

    def current_scores(self) -> list[dict]:
        return [score for score in self.history if score["status"] == "active"]

