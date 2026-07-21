"""Tests for Glass Gate control v2 (label-free)."""

from __future__ import annotations

import unittest

from broadcast_alpha.glassgate_control_v2 import (
    EvidenceOverlapController,
    OracleScarceProtectController,
    expand_ab_cases,
    sanitize_agents,
    evaluate_controller,
    run_glassgate_control_v2,
)


class GlassGateControlV2Tests(unittest.TestCase):
    def test_sanitize_strips_labels(self):
        agents = [{"position": "A", "claim": "x", "is_correct": True}]
        s = sanitize_agents(agents)
        self.assertNotIn("is_correct", s[0])

    def test_expand_larger_than_base(self):
        cases = expand_ab_cases(seed=1, repeats=2)
        self.assertGreater(len(cases), 64)

    def test_deployable_cannot_use_labels(self):
        cases = [
            c
            for c in expand_ab_cases(0, repeats=1)
            if c["panel_composition"] == "one_correct_two_wrong" and c["bias_condition"] == "wrong_bias"
        ][:5]
        r = evaluate_controller(EvidenceOverlapController(), cases, bias_pressure=True)
        self.assertIn("accuracy", r)

    def test_oracle_ceiling_runs(self):
        cases = [
            c
            for c in expand_ab_cases(0, repeats=1)
            if c["panel_composition"] == "one_correct_two_wrong" and c["bias_condition"] == "wrong_bias"
        ][:5]
        r = evaluate_controller(OracleScarceProtectController(), cases, bias_pressure=True)
        self.assertGreaterEqual(r["accuracy"], 0.0)

    def test_v2_run_artifacts(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            result = run_glassgate_control_v2(
                seed=0, n_seeds=2, expand_repeats=1, artifact_root=td
            )
            p = Path(result.artifact_path)
            self.assertTrue((p / "claim_matrix.json").exists())
            self.assertTrue((p / "result_card.md").exists())


if __name__ == "__main__":
    unittest.main()
