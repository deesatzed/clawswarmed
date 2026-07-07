def assert_single_token(label: str) -> str:
    if len(label.strip().split()) != 1:
        raise ValueError(f"verdict label must be a single token: {label!r}")
    return label


class NullJLensProbe:
    def run(self, verdict_label: str, evidence_text: str) -> dict:
        assert_single_token(verdict_label)
        return {
            "status": "unavailable",
            "reason": "real J-lens source/model access has not been verified",
            "verdict_label": verdict_label,
            "evidence_chars": len(evidence_text),
            "layer_position_activation": [],
        }

