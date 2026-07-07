import random

from .contracts import Candidate


def random_gate(candidates: list[Candidate], k: int, seed: int) -> list[Candidate]:
    rng = random.Random(seed)
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    return shuffled[:k]


def naive_topk(candidates: list[Candidate], k: int) -> list[Candidate]:
    return sorted(candidates, key=lambda candidate: candidate.score, reverse=True)[:k]


def scarce_protected(candidates: list[Candidate], k: int = 7) -> list[Candidate]:
    selected: list[Candidate] = []
    selected_ids: set[str] = set()

    def add(candidate: Candidate | None) -> None:
        if candidate is None or candidate.id in selected_ids or len(selected) >= k:
            return
        selected.append(candidate)
        selected_ids.add(candidate.id)

    high_conf = [c for c in candidates if c.slot_type == "high_confidence"]
    for candidate in naive_topk(high_conf, min(3, k)):
        add(candidate)

    for slot_type in [
        "highest_disagreement",
        "minority_report",
        "risk_if_suppressed",
        "verifier_action",
    ]:
        slot_candidates = [c for c in candidates if c.slot_type == slot_type]
        add(naive_topk(slot_candidates, 1)[0] if slot_candidates else None)

    for candidate in naive_topk([c for c in candidates if c.id not in selected_ids], k - len(selected)):
        add(candidate)

    return selected

