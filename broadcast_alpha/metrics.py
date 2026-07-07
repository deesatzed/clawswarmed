from statistics import mean


def discrimination(correct_influenced: int, correct_total: int, incorrect_influenced: int, incorrect_total: int) -> float:
    if correct_total == 0 or incorrect_total == 0:
        raise ValueError("totals must be non-zero")
    return (correct_influenced / correct_total) - (incorrect_influenced / incorrect_total)


def glassgate_lift(d_by_arm: dict[str, float]) -> float:
    controls = [d_by_arm["abundant"], d_by_arm["random"], d_by_arm["scarce_naive_topk"]]
    return d_by_arm["scarce_protected"] - max(controls)


def seed_camouflage_failed(auc: float | None, tolerance: float = 0.1) -> bool:
    if auc is None:
        return False
    return abs(auc - 0.5) > tolerance


def candidate_ablation_influence(original_passed: bool, ablated_passed: bool) -> bool:
    return original_passed != ablated_passed


def simple_ci(values: list[float]) -> list[float]:
    if not values:
        return [0.0, 0.0]
    center = mean(values)
    spread = 0.0 if len(values) == 1 else max(abs(value - center) for value in values)
    return [round(center - spread, 6), round(center + spread, 6)]

