import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


class BroadcastAlphaTests(unittest.TestCase):
    def test_contracts_include_task_and_metrics_records(self):
        from broadcast_alpha.contracts import MetricsRecord, Task

        task = Task(id="task_001", suite="codebug", verifier="hidden_tests")
        metrics = MetricsRecord(
            run_id="run_001",
            prereg_id="PREREG_DSH-01",
            glassgate_lift=0.3,
            glassgate_lift_ci95=[0.2, 0.4],
        )

        self.assertEqual(task.to_dict()["verifier"], "hidden_tests")
        self.assertEqual(metrics.to_dict()["glassgate_lift"], 0.3)

    def test_ledger_append_and_verify_10k(self):
        from broadcast_alpha.ledger import Ledger

        ledger = Ledger()
        for index in range(10_000):
            ledger.append(kind="submission", body={"index": index}, evaluator_id="eval_0", epoch_id="epoch_0")

        self.assertEqual(len(ledger.receipts), 10_000)
        self.assertTrue(ledger.verify_chain())

    def test_ledger_tamper_detection(self):
        from broadcast_alpha.ledger import Ledger

        ledger = Ledger()
        ledger.append(kind="submission", body={"claim": "original"})
        ledger.append(kind="decision", body={"admit": True})
        ledger.receipts[0].body["claim"] = "tampered"

        self.assertFalse(ledger.verify_chain())

    def test_replay_byte_exact(self):
        from broadcast_alpha.experiments import run_synthetic
        from broadcast_alpha.replay import replay_context

        with tempfile.TemporaryDirectory() as tmp:
            result = run_synthetic(seed=42, artifact_root=Path(tmp))
            context = replay_context(result.artifact_path, agent_id="agent_1", step=3)

            self.assertEqual(context, result.expected_replay["agent_1"]["3"])

    def test_discrimination_formula(self):
        from broadcast_alpha.metrics import discrimination

        self.assertAlmostEqual(discrimination(6, 10, 2, 10), 0.4)

    def test_glassgate_lift_formula(self):
        from broadcast_alpha.metrics import glassgate_lift

        d_by_arm = {
            "abundant": 0.1,
            "random": 0.2,
            "scarce_naive_topk": 0.0,
            "scarce_protected": 0.5,
        }

        self.assertAlmostEqual(glassgate_lift(d_by_arm), 0.3)

    def test_random_gate_reproducibility(self):
        from broadcast_alpha.contracts import Candidate
        from broadcast_alpha.gate import random_gate

        candidates = [Candidate(id=f"cand_{i}", score=i / 10, slot_type="high_confidence") for i in range(10)]

        first = random_gate(candidates, k=4, seed=17)
        second = random_gate(candidates, k=4, seed=17)

        self.assertEqual([c.id for c in first], [c.id for c in second])

    def test_naive_topk_orders_by_score(self):
        from broadcast_alpha.contracts import Candidate
        from broadcast_alpha.gate import naive_topk

        candidates = [
            Candidate(id="low", score=0.1, slot_type="high_confidence"),
            Candidate(id="high", score=0.9, slot_type="high_confidence"),
            Candidate(id="mid", score=0.5, slot_type="high_confidence"),
        ]

        self.assertEqual([c.id for c in naive_topk(candidates, k=2)], ["high", "mid"])

    def test_protected_gate_reserves_dissent_slots(self):
        from broadcast_alpha.contracts import Candidate
        from broadcast_alpha.gate import scarce_protected

        candidates = [
            Candidate(id="conf_a", score=0.9, slot_type="high_confidence"),
            Candidate(id="conf_b", score=0.8, slot_type="high_confidence"),
            Candidate(id="conf_c", score=0.7, slot_type="high_confidence"),
            Candidate(id="conf_d", score=0.6, slot_type="high_confidence"),
            Candidate(id="minority", score=0.2, slot_type="minority_report"),
            Candidate(id="risk", score=0.1, slot_type="risk_if_suppressed"),
            Candidate(id="disagree", score=0.3, slot_type="highest_disagreement"),
            Candidate(id="verify", score=0.4, slot_type="verifier_action"),
        ]

        selected = scarce_protected(candidates, k=7)
        selected_ids = {candidate.id for candidate in selected}

        self.assertIn("minority", selected_ids)
        self.assertIn("risk", selected_ids)
        self.assertIn("disagree", selected_ids)
        self.assertIn("verify", selected_ids)

    def test_seed_camouflage_auc_flag(self):
        from broadcast_alpha.metrics import seed_camouflage_failed

        self.assertTrue(seed_camouflage_failed(0.75, tolerance=0.1))
        self.assertFalse(seed_camouflage_failed(0.53, tolerance=0.1))

    def test_candidate_ablation_changes_influence(self):
        from broadcast_alpha.metrics import candidate_ablation_influence

        self.assertTrue(candidate_ablation_influence(original_passed=True, ablated_passed=False))
        self.assertFalse(candidate_ablation_influence(original_passed=True, ablated_passed=True))

    def test_epoch_tombstone_masks_current_authority_but_preserves_history(self):
        from broadcast_alpha.epochs import EpochAuthority

        authority = EpochAuthority(active_evaluator="eval_a")
        authority.add_score("score_1", evaluator_id="eval_a", value=0.7)
        authority.tombstone_evaluator("eval_a", reason="replaced at epoch boundary")

        self.assertEqual(authority.current_scores(), [])
        self.assertEqual(len(authority.history), 1)
        self.assertEqual(authority.history[0]["status"], "tombstoned")

    def test_single_token_verdict_assertion(self):
        from broadcast_alpha.jlens import assert_single_token

        self.assertEqual(assert_single_token("yes"), "yes")
        with self.assertRaises(ValueError):
            assert_single_token("not sure")

    def test_null_jlens_probe_interface(self):
        from broadcast_alpha.jlens import NullJLensProbe

        result = NullJLensProbe().run("admit", "evidence text")

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("source", result["reason"])

    def test_jlens_gate_freezes_without_exact_source_or_white_box_model(self):
        from broadcast_alpha.jlens import run_jlens_gate

        with tempfile.TemporaryDirectory() as tmp:
            result = run_jlens_gate(seed=42, artifact_root=Path(tmp))
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            sources = json.loads((result.artifact_path / "sources.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(metrics["rail_status"], "frozen")
        self.assertFalse(metrics["required_exact_source_found"])
        self.assertFalse(metrics["white_box_model_available"])
        self.assertFalse(metrics["real_probe_runnable"])
        self.assertEqual(metrics["failure_ledger_entry_id"], "JLENS-FREEZE-001")
        self.assertIn(
            "Verbalizable Representations Form a Global Workspace",
            " ".join(sources["searched_queries"]),
        )
        self.assertTrue(
            any(source["url"] == "https://arxiv.org/abs/2309.16042" for source in sources["verified_adjacent_sources"])
        )
        self.assertTrue(
            any(
                source["url"] == "https://github.com/TransformerLensOrg/TransformerLens"
                for source in sources["verified_adjacent_sources"]
            )
        )
        self.assertIn('"kind": "jlens_gate_decision"', ledger)
        self.assertIn("J-lens rail frozen", result_card)

    def test_jlens_gate_single_token_label_manifest(self):
        from broadcast_alpha.jlens import verify_single_token_labels

        labels = ["yes", "no", "admit", "reject", "pass", "fail"]

        self.assertEqual(
            verify_single_token_labels(labels),
            {label: True for label in labels},
        )
        with self.assertRaises(ValueError):
            verify_single_token_labels(["yes", "not sure"])

    def test_metrics_json_schema(self):
        from broadcast_alpha.experiments import run_synthetic

        with tempfile.TemporaryDirectory() as tmp:
            result = run_synthetic(seed=42, artifact_root=Path(tmp))
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())

        required = {
            "run_id",
            "prereg_id",
            "glassgate_lift",
            "glassgate_lift_ci95",
            "D_by_arm",
            "D_by_panel_type",
            "verified_solve_rate",
            "influence_correct",
            "influence_incorrect",
            "panel_correlation_rho",
            "seed_detectability_auc",
            "premature_convergence_pc",
            "pc_d_corr",
            "intervention_delta_D",
            "token_cost_per_solve",
            "replay_bundle_path",
            "result_card_path",
        }
        self.assertTrue(required.issubset(metrics))

    def test_result_card_generation(self):
        from broadcast_alpha.experiments import run_synthetic

        with tempfile.TemporaryDirectory() as tmp:
            result = run_synthetic(seed=42, artifact_root=Path(tmp))
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertIn("GLASSGATE_LIFT", result_card)
        self.assertIn("D by arm", result_card)
        self.assertIn("Replay", result_card)

    def test_cli_run_synthetic_creates_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, "-m", "broadcast_alpha", "run-synthetic", "--seed", "42", "--artifact-root", tmp],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])

            self.assertTrue((artifact_path / "metrics.json").exists())
            self.assertTrue((artifact_path / "result_card.md").exists())

    def test_cli_run_jlens_gate_creates_freeze_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, "-m", "broadcast_alpha", "run-jlens-gate", "--seed", "42", "--artifact-root", tmp],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])
            metrics = json.loads((artifact_path / "metrics.json").read_text())

            self.assertTrue((artifact_path / "sources.json").exists())
            self.assertTrue((artifact_path / "result_card.md").exists())
            self.assertEqual(metrics["rail_status"], "frozen")

            export = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "export-ledger",
                    str(artifact_path),
                    "--format",
                    "jsonl",
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            self.assertTrue(json.loads(export.stdout)["verified"])

            replay = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "replay",
                    str(artifact_path),
                    "--agent",
                    "agent_1",
                    "--step",
                    "3",
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            self.assertIn("J-lens rail frozen", replay.stdout)

    def test_codebug_task_bank_hidden_tests_distinguish_seeded_patches(self):
        from broadcast_alpha.task_bank import load_codebug_tasks, verify_patch

        tasks = load_codebug_tasks()

        self.assertGreaterEqual(len(tasks), 30)
        self.assertEqual(len({task.id for task in tasks}), len(tasks))
        for task in tasks[:30]:
            self.assertGreaterEqual(len(task.hidden_tests), 3)
            self.assertNotIn(str(task.hidden_tests[0].expected), task.public_prompt)
            self.assertTrue(verify_patch(task, task.correct_patch).passed, task.id)
            self.assertFalse(verify_patch(task, task.incorrect_patch).passed, task.id)

    def test_run_dsh_records_task_level_hidden_test_outcomes(self):
        from broadcast_alpha.experiments import run_dsh

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dsh(
                prereg_path=APP_ROOT / "prereg" / "PREREG_DSH-01.md",
                seed=42,
                tasks_per_cell=5,
                artifact_root=Path(tmp),
            )
            task_runs = json.loads((result.artifact_path / "task_runs.json").read_text())
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()

        self.assertEqual(len(task_runs["runs"]), 24 * 5)
        self.assertGreaterEqual(metrics["task_bank_size"], 30)
        self.assertEqual(metrics["ci_method"], "bootstrap_resample_task_outcomes")
        self.assertGreaterEqual(metrics["bootstrap_samples"], 200)
        sample = task_runs["runs"][0]
        required = {
            "task_id",
            "panel_type",
            "workspace_arm",
            "seed_condition",
            "selected_candidate_id",
            "hidden_verifier_passed",
            "correct_patch_passes",
            "incorrect_patch_passes",
            "candidate_ablation_changed",
            "influenced",
        }
        self.assertTrue(required.issubset(sample))
        self.assertTrue(sample["correct_patch_passes"])
        self.assertFalse(sample["incorrect_patch_passes"])
        self.assertIn('"kind": "task_result"', ledger)

    def test_run_dsh_builds_balanced_24_cell_grid(self):
        from broadcast_alpha.experiments import run_dsh

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dsh(
                prereg_path=APP_ROOT / "prereg" / "PREREG_DSH-01.md",
                seed=42,
                tasks_per_cell=30,
                artifact_root=Path(tmp),
            )
            grid = json.loads((result.artifact_path / "grid.json").read_text())
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())

        self.assertEqual(len(grid["cells"]), 24)
        self.assertTrue(all(cell["task_count"] == 30 for cell in grid["cells"]))
        self.assertEqual(metrics["cell_count"], 24)
        self.assertEqual(metrics["task_count_per_cell"], 30)
        self.assertEqual(metrics["total_task_runs"], 720)
        self.assertIn("candidate_ablation_rate", metrics)
        self.assertEqual(set(metrics["D_by_arm"]), {"abundant", "random", "scarce_naive_topk", "scarce_protected"})
        self.assertEqual(len(metrics["glassgate_lift_ci95"]), 2)

    def test_cli_run_dsh_creates_macro_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-dsh",
                    "--prereg",
                    "prereg/PREREG_DSH-01.md",
                    "--seed",
                    "42",
                    "--tasks-per-cell",
                    "30",
                    "--artifact-root",
                    tmp,
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])
            result_card = (artifact_path / "result_card.md").read_text()

            self.assertTrue((artifact_path / "metrics.json").exists())
            self.assertTrue((artifact_path / "grid.json").exists())
            self.assertIn("24-cell DSH grid", result_card)

    def test_run_rqgm_builds_5_epoch_controlled_trajectory(self):
        from broadcast_alpha.experiments import run_rqgm

        with tempfile.TemporaryDirectory() as tmp:
            result = run_rqgm(
                prereg_path=APP_ROOT / "prereg" / "PREREG_EPOCH-01.md",
                seed=42,
                epochs=5,
                artifact_root=Path(tmp),
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            trajectory = json.loads((result.artifact_path / "trajectory.json").read_text())
            authority = json.loads((result.artifact_path / "authority.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(metrics["epoch_count"], 5)
        self.assertEqual(len(trajectory["epochs"]), 5)
        self.assertGreaterEqual(metrics["replacement_count"], 1)
        self.assertEqual(metrics["active_jlens_veto"], False)
        self.assertIn("5-epoch RQGM", result_card)
        self.assertTrue(all(epoch["frozen_semantics"] for epoch in trajectory["epochs"]))
        self.assertTrue(all(epoch["held_out_anchor_task_count"] >= 30 for epoch in trajectory["epochs"]))
        self.assertTrue(all(epoch["replacement_decision"]["reason_codes"] for epoch in trajectory["epochs"]))
        self.assertTrue(any(epoch["replacement_decision"]["accepted"] for epoch in trajectory["epochs"]))
        tombstoned_ids = {
            score["evaluator_id"]
            for score in authority["history"]
            if score["status"] == "tombstoned"
        }
        current_ids = {score["evaluator_id"] for score in authority["current_scores"]}
        self.assertTrue(tombstoned_ids)
        self.assertTrue(tombstoned_ids.isdisjoint(current_ids))
        self.assertIn('"kind": "replacement_decision"', ledger)
        self.assertIn('"kind": "tombstone"', ledger)

    def test_cli_run_rqgm_creates_epoch_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-rqgm",
                    "--prereg",
                    "prereg/PREREG_EPOCH-01.md",
                    "--seed",
                    "42",
                    "--epochs",
                    "5",
                    "--artifact-root",
                    tmp,
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])
            metrics = json.loads((artifact_path / "metrics.json").read_text())

            self.assertTrue((artifact_path / "trajectory.json").exists())
            self.assertTrue((artifact_path / "authority.json").exists())
            self.assertEqual(metrics["epoch_count"], 5)
            replay = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "replay",
                    str(artifact_path),
                    "--agent",
                    "agent_1",
                    "--step",
                    "3",
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            self.assertIn("epoch 3", replay.stdout)


if __name__ == "__main__":
    unittest.main()
