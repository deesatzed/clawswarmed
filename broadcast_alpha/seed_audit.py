import re

from .metrics import seed_camouflage_failed


LEAK_MARKERS = ("correct_minority", "incorrect_minority", "minority", "seeded", "seed")
PUBLIC_FEATURE_FIELDS = ["selected_candidate_id"]


def roc_auc(labels: list[int], scores: list[float]) -> float:
    if len(labels) != len(scores):
        raise ValueError("labels and scores must have the same length")
    positives = [score for label, score in zip(labels, scores, strict=True) if label == 1]
    negatives = [score for label, score in zip(labels, scores, strict=True) if label == 0]
    if not positives or not negatives:
        raise ValueError("auc requires at least one positive and one negative")

    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def _public_text(row: dict, fields: list[str]) -> str:
    return " ".join(str(row.get(field, "")) for field in fields).lower()


def _seed_label(row: dict) -> int:
    if row.get("selected_candidate_seed_status") == "seeded":
        return 1
    if row.get("influence_source") in {"correct_minority", "incorrect_minority"}:
        return 1
    return 0


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def adversarial_token_auc(labels: list[int], texts: list[str]) -> float:
    if len(labels) != len(texts):
        raise ValueError("labels and texts must have the same length")
    base_rate = sum(labels) / len(labels)
    token_counts: dict[str, list[int]] = {}
    for label, text in zip(labels, texts, strict=True):
        for token in set(_tokens(text)):
            counts = token_counts.setdefault(token, [0, 0])
            counts[0] += label
            counts[1] += 1
    token_rates = {
        token: positive / total
        for token, (positive, total) in token_counts.items()
        if total
    }
    scores = [
        max((token_rates[token] for token in set(_tokens(text)) if token in token_rates), default=base_rate)
        for text in texts
    ]
    return roc_auc(labels, scores)


def audit_seed_detectability(
    task_runs: list[dict],
    tolerance: float = 0.1,
    public_feature_fields: list[str] | None = None,
) -> dict:
    fields = public_feature_fields or PUBLIC_FEATURE_FIELDS
    labels = [_seed_label(row) for row in task_runs]
    marker_scores = []
    public_texts = []
    leak_markers_found = set()
    for row in task_runs:
        text = _public_text(row, fields)
        public_texts.append(text)
        row_markers = [marker for marker in LEAK_MARKERS if marker in text]
        if row_markers:
            leak_markers_found.update(row_markers)
            marker_scores.append(1.0)
        else:
            marker_scores.append(0.0)

    marker_auc = round(roc_auc(labels, marker_scores), 6)
    adversarial_auc = round(adversarial_token_auc(labels, public_texts), 6)
    auc = max(marker_auc, adversarial_auc)
    marker_failed = seed_camouflage_failed(marker_auc, tolerance=tolerance)
    adversarial_failed = seed_camouflage_failed(adversarial_auc, tolerance=tolerance)
    failed = marker_failed or adversarial_failed
    return {
        "auditor": "marker_and_adversarial_token_auc_v1",
        "auc": auc,
        "marker_auc": marker_auc,
        "adversarial_auc": adversarial_auc,
        "tolerance": tolerance,
        "camouflage_passed": not failed,
        "seed_camouflage_failed": failed,
        "marker_camouflage_failed": marker_failed,
        "adversarial_camouflage_failed": adversarial_failed,
        "positive_count": sum(labels),
        "negative_count": len(labels) - sum(labels),
        "public_feature_fields": fields,
        "leak_markers": list(LEAK_MARKERS),
        "leak_markers_found": sorted(leak_markers_found),
        "score_distribution": {
            "positive_marker_score_count": sum(
                1 for label, score in zip(labels, marker_scores, strict=True) if label == 1 and score == 1.0
            ),
            "negative_marker_score_count": sum(
                1 for label, score in zip(labels, marker_scores, strict=True) if label == 0 and score == 1.0
            ),
        },
    }
