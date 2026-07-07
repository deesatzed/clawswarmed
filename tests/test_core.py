import json
import subprocess
import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


class EvidenceInventoryTests(unittest.TestCase):
    def test_inventory_loads_workspace_evidence_with_roles(self):
        from claswarmed.evidence import build_inventory

        inventory = build_inventory(APP_ROOT.parent)

        by_path = {item["path"]: item for item in inventory["items"]}
        self.assertEqual(by_path["bld1.md"]["role"], "product vision")
        self.assertEqual(by_path["bld2.md"]["role"], "runtime foundation review")
        self.assertEqual(by_path["bld3.md"]["role"], "RQGM/EvoClaw architecture plan")
        self.assertEqual(by_path["2606.26294v2.pdf"]["kind"], "paper")
        self.assertTrue(by_path["swarm-code/"]["present"])

    def test_build_plan_names_core_phases(self):
        from claswarmed.planner import build_showpiece_plan

        plan = build_showpiece_plan("claswarmed")

        phase_names = [phase["name"] for phase in plan["phases"]]
        self.assertIn("Evidence Inventory", phase_names)
        self.assertIn("Council Planning", phase_names)
        self.assertIn("RQGM Epoch Demo", phase_names)
        self.assertIn("Dashboard Proof", phase_names)


class RqgmTests(unittest.TestCase):
    def test_epoch_replaces_evaluator_only_when_challenger_beats_margin(self):
        from claswarmed.rqgm import EvaluatorSlot, consider_replacement

        slot = EvaluatorSlot(name="code-review", incumbent="claude-reviewer", score=0.72)

        keep = consider_replacement(slot, challenger="grok-reviewer", challenger_score=0.73)
        replace = consider_replacement(slot, challenger="gemini-reviewer", challenger_score=0.80)

        self.assertFalse(keep.replaced)
        self.assertEqual(keep.active_evaluator, "claude-reviewer")
        self.assertTrue(replace.replaced)
        self.assertEqual(replace.active_evaluator, "gemini-reviewer")
        self.assertIn("epoch boundary", replace.rationale)


class CliTests(unittest.TestCase):
    def test_cli_inventory_outputs_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "claswarmed", "inventory", "--json"],
            cwd=APP_ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["project"], "claswarmed")
        self.assertGreaterEqual(len(payload["items"]), 5)


if __name__ == "__main__":
    unittest.main()

