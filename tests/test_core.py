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

    def test_role_plan_assigns_models_and_review_gates(self):
        from claswarmed.planner import build_role_plan

        role_plan = build_role_plan("Build claswarmed Phase 2", APP_ROOT.parent)

        role_names = {role["model"]: role for role in role_plan["roles"]}
        self.assertEqual(role_names["Codex"]["primary_job"], "program manager")
        self.assertEqual(role_names["Grok"]["primary_job"], "architecture critic")
        self.assertEqual(role_names["Claude"]["primary_job"], "code quality reviewer")
        self.assertEqual(role_names["Gemini"]["primary_job"], "long-context analyst")
        self.assertIn("OpenAI-compatible profile", role_names)

        gate_names = [gate["name"] for gate in role_plan["review_gates"]]
        self.assertIn("source-evidence boundary", gate_names)
        self.assertIn("council synthesis", gate_names)
        self.assertIn("rqgm evaluator checkpoint", gate_names)

    def test_council_plan_matches_fusion_panel_shape(self):
        from claswarmed.council import build_council_plan

        council_plan = build_council_plan("Assess Phase 2 risks", APP_ROOT.parent)

        perspectives = [panel["perspective"] for panel in council_plan["panels"]]
        self.assertEqual(perspectives, ["architect", "skeptic", "operator"])
        self.assertEqual(council_plan["judge"]["tool_policy"], "no-tools")
        self.assertEqual(council_plan["panels"][0]["tool_policy"], "read-only")
        self.assertIn("consensus", council_plan["synthesis_schema"])
        self.assertIn("blind_spots", council_plan["synthesis_schema"])

    def test_run_receipt_persists_council_plan_manifest(self):
        from claswarmed.council import build_council_plan
        from claswarmed.receipts import save_run_receipt

        council_plan = build_council_plan("Persist Phase 2 receipt", APP_ROOT.parent)
        receipt = save_run_receipt(APP_ROOT, "council-plan", council_plan)

        self.assertTrue(Path(receipt["path"]).exists())
        loaded = json.loads(Path(receipt["path"]).read_text())
        self.assertEqual(loaded["kind"], "council-plan")
        self.assertEqual(loaded["payload"]["project"], "claswarmed")
        Path(receipt["path"]).unlink()


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


class DashboardTests(unittest.TestCase):
    def test_dashboard_renders_council_panel(self):
        from claswarmed.dashboard import render_dashboard

        html = render_dashboard(APP_ROOT.parent)

        self.assertIn("Council Plan", html)
        self.assertIn("architect", html)
        self.assertIn("skeptic", html)
        self.assertIn("operator", html)


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

    def test_cli_council_plan_outputs_json_and_can_persist_receipt(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "claswarmed",
                "council-plan",
                "--goal",
                "Build Phase 2",
                "--save",
                "--json",
            ],
            cwd=APP_ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["project"], "claswarmed")
        self.assertIn("receipt", payload)
        self.assertTrue(Path(payload["receipt"]["path"]).exists())
        Path(payload["receipt"]["path"]).unlink()


if __name__ == "__main__":
    unittest.main()
