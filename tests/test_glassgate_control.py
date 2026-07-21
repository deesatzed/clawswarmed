"""Tests for Glass Gate control layer."""

from __future__ import annotations

import unittest

from broadcast_alpha.ab_bias_suite import generate_ab_cases
from broadcast_alpha.glassgate_control import (
    DissentBoostController,
    EqualController,
    ScarceProtectController,
    evaluate_controller,
    run_glassgate_control,
)


class GlassGateControlTests(unittest.TestCase):
    def test_generate_minority_cases(self):
        cases = [c for c in generate_ab_cases(42) if c["panel_composition"] == "one_correct_two_wrong"]
        self.assertGreater(len(cases), 0)

    def test_scarce_protect_beats_equal_on_wrong_bias(self):
        cases = [
            c
            for c in generate_ab_cases(42)
            if c["panel_composition"] == "one_correct_two_wrong" and c["bias_condition"] == "wrong_bias"
        ]
        eq = evaluate_controller(EqualController(), cases, bias_pressure=True)
        sp = evaluate_controller(ScarceProtectController(), cases, bias_pressure=True)
        self.assertGreaterEqual(sp["accuracy"], eq["accuracy"])

    def test_dissent_boost_no_label_leak_runs(self):
        cases = [
            c
            for c in generate_ab_cases(0)
            if c["panel_composition"] == "one_correct_two_wrong" and c["bias_condition"] == "wrong_bias"
        ]
        r = evaluate_controller(DissentBoostController(), cases, bias_pressure=True)
        self.assertIn("accuracy", r)

    def test_official_run_writes_artifacts(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            result = run_glassgate_control(seed=42, artifact_root=td)
            p = Path(result.artifact_path)
            self.assertTrue((p / "claim_matrix.json").exists())
            self.assertTrue((p / "result_card.md").exists())
            self.assertTrue((p / "metrics.json").exists())


if __name__ == "__main__":
    unittest.main()
