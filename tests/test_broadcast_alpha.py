import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


def _without_openrouter_env() -> dict:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("OPENROUTER_")
    }


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

    def test_seed_detectability_auc_handles_ties(self):
        from broadcast_alpha.seed_audit import roc_auc

        self.assertAlmostEqual(roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]), 0.75)
        self.assertAlmostEqual(roc_auc([0, 0, 1, 1], [0.0, 0.0, 0.0, 0.0]), 0.5)

    def test_seed_adversarial_audit_detects_public_id_leakage(self):
        from broadcast_alpha.seed_audit import audit_seed_detectability

        rows = [
            {"selected_candidate_id": "seeded_patch_a", "selected_candidate_seed_status": "seeded"},
            {"selected_candidate_id": "seeded_patch_b", "selected_candidate_seed_status": "seeded"},
            {"selected_candidate_id": "ordinary_patch_a", "selected_candidate_seed_status": "unseeded"},
            {"selected_candidate_id": "ordinary_patch_b", "selected_candidate_seed_status": "unseeded"},
        ]

        audit = audit_seed_detectability(rows)

        self.assertEqual(audit["marker_auc"], 1.0)
        self.assertEqual(audit["adversarial_auc"], 1.0)
        self.assertTrue(audit["seed_camouflage_failed"])
        self.assertTrue(audit["adversarial_camouflage_failed"])
        self.assertIn("seeded", audit["leak_markers_found"])

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

    def test_live_gate_records_provider_presence_without_secret_values(self):
        from broadcast_alpha.live_gate import run_live_gate

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text(
                "OPENROUTER_API_KEY=dummy-secret-value\nOPENROUTER_MODEL=test/model\n"
            )
            result = run_live_gate(seed=42, artifact_root=tmp_path, env_file=env_file, env={})
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            provider_status = json.loads((result.artifact_path / "provider_status.json").read_text())
            combined_artifacts = "\n".join(
                [
                    (result.artifact_path / "metrics.json").read_text(),
                    (result.artifact_path / "provider_status.json").read_text(),
                    (result.artifact_path / "result_card.md").read_text(),
                    (result.artifact_path / "ledger.jsonl").read_text(),
                ]
            )

        self.assertEqual(metrics["rail_status"], "gated_ready_no_spend")
        self.assertTrue(metrics["openrouter_api_key_present"])
        self.assertFalse(metrics["api_spend_authorized"])
        self.assertFalse(metrics["network_probe_run"])
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertIn("api_spend_not_authorized", metrics["reason_codes"])
        self.assertEqual(
            provider_status["required_env"]["OPENROUTER_API_KEY"],
            {"present": True, "value_recorded": False},
        )
        self.assertEqual(
            provider_status["required_env"]["OPENROUTER_MODEL"],
            {"present": True, "value_recorded": False},
        )
        self.assertNotIn("dummy-secret-value", combined_artifacts)
        self.assertIn('"kind": "live_gate_decision"', combined_artifacts)
        self.assertIn("No API call was made", combined_artifacts)

    def test_live_gate_requires_execute_live_even_when_spend_is_authorized(self):
        from broadcast_alpha.live_gate import run_live_gate

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\n")
            result = run_live_gate(
                seed=42,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=False,
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()

        self.assertEqual(metrics["rail_status"], "configured_not_executed")
        self.assertFalse(metrics["adapter_call_performed"])
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertIn("execute_live_not_requested", metrics["reason_codes"])
        self.assertNotIn("dummy-secret-value", ledger)

    def test_live_gate_fake_transport_execution_is_replayable_and_sanitized(self):
        from broadcast_alpha.live_gate import run_live_gate

        captured_requests = []

        def fake_transport(request):
            captured_requests.append(request)
            return {
                "id": "chatcmpl_fake",
                "choices": [{"message": {"content": "minority insight admitted"}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16},
            }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\nOPENROUTER_MODEL=test/model\n")
            result = run_live_gate(
                seed=42,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=True,
                transport=fake_transport,
                transport_label="fake",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            provider_status = json.loads((result.artifact_path / "provider_status.json").read_text())
            combined_artifacts = "\n".join(
                [
                    (result.artifact_path / "metrics.json").read_text(),
                    (result.artifact_path / "provider_status.json").read_text(),
                    (result.artifact_path / "result_card.md").read_text(),
                    (result.artifact_path / "ledger.jsonl").read_text(),
                    (result.artifact_path / "replay" / "contexts.json").read_text(),
                ]
            )

        self.assertEqual(metrics["rail_status"], "adapter_executed_fake_transport")
        self.assertTrue(metrics["adapter_call_performed"])
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertEqual(metrics["transport_label"], "fake")
        self.assertEqual(metrics["adapter_response"]["response_id_present"], True)
        self.assertEqual(metrics["adapter_response"]["content_preview"], "minority insight admitted")
        self.assertEqual(metrics["adapter_response"]["usage_total_tokens"], 16)
        self.assertEqual(provider_status["model_configured"], True)
        self.assertEqual(len(captured_requests), 1)
        self.assertEqual(captured_requests[0]["body"]["model"], "test/model")
        self.assertIn("Bearer dummy-secret-value", captured_requests[0]["headers"]["Authorization"])
        self.assertNotIn("dummy-secret-value", combined_artifacts)
        self.assertIn('"kind": "adapter_response"', combined_artifacts)
        self.assertIn("fake transport", combined_artifacts)

    def test_live_gate_missing_key_records_unavailable(self):
        from broadcast_alpha.live_gate import run_live_gate

        with tempfile.TemporaryDirectory() as tmp:
            result = run_live_gate(seed=42, artifact_root=Path(tmp), env={})
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            replay = json.loads((result.artifact_path / "replay" / "contexts.json").read_text())

        self.assertEqual(metrics["rail_status"], "unavailable")
        self.assertFalse(metrics["openrouter_api_key_present"])
        self.assertIn("missing_openrouter_api_key", metrics["reason_codes"])
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertIn("No live model run", replay["agent_1"]["3"])

    def test_cli_run_live_gate_creates_replayable_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\n")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-live-gate",
                    "--seed",
                    "42",
                    "--artifact-root",
                    str(tmp_path / "artifacts"),
                    "--env-file",
                    str(env_file),
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                env=_without_openrouter_env(),
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])
            metrics = json.loads((artifact_path / "metrics.json").read_text())

            self.assertEqual(metrics["rail_status"], "gated_ready_no_spend")
            self.assertTrue((artifact_path / "provider_status.json").exists())

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
            self.assertIn("No live model run", replay.stdout)

    def test_cli_run_live_gate_authorized_without_execute_stays_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\n")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-live-gate",
                    "--seed",
                    "42",
                    "--artifact-root",
                    str(tmp_path / "artifacts"),
                    "--env-file",
                    str(env_file),
                    "--authorize-api-spend",
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                env=_without_openrouter_env(),
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])
            metrics = json.loads((artifact_path / "metrics.json").read_text())
            artifacts = "\n".join(
                [
                    (artifact_path / "metrics.json").read_text(),
                    (artifact_path / "provider_status.json").read_text(),
                    (artifact_path / "result_card.md").read_text(),
                    (artifact_path / "ledger.jsonl").read_text(),
                ]
            )

        self.assertEqual(metrics["rail_status"], "configured_not_executed")
        self.assertFalse(metrics["adapter_call_performed"])
        self.assertIn("execute_live_not_requested", metrics["reason_codes"])
        self.assertNotIn("dummy-secret-value", artifacts)

    def test_live_dsh_default_blocks_without_adapter_execution(self):
        from broadcast_alpha.live_dsh import run_live_dsh

        with tempfile.TemporaryDirectory() as tmp:
            result = run_live_dsh(seed=42, tasks_per_cell=1, artifact_root=Path(tmp), env={})
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            task_runs = json.loads((result.artifact_path / "task_runs.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(metrics["run_status"], "blocked_no_live_execution")
        self.assertEqual(metrics["cell_count"], 24)
        self.assertEqual(metrics["planned_task_runs"], 24)
        self.assertEqual(metrics["task_run_count"], 0)
        self.assertEqual(metrics["adapter_call_count"], 0)
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertIn("missing_openrouter_api_key", metrics["reason_codes"])
        self.assertEqual(task_runs["runs"], [])
        self.assertIn('"kind": "live_dsh_blocked"', ledger)
        self.assertIn("Live DSH pilot blocked", result_card)

    def test_live_dsh_fake_transport_runs_balanced_pilot_without_secret_values(self):
        from broadcast_alpha.live_dsh import run_live_dsh

        captured_requests = []

        def fake_transport(request):
            captured_requests.append(request)
            return {
                "id": f"chatcmpl_fake_{len(captured_requests)}",
                "choices": [{"message": {"content": "{\"patch\": \"x + 2\", \"rationale\": \"repair add\"}"}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 3, "total_tokens": 12},
            }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\nOPENROUTER_MODEL=test/model\n")
            result = run_live_dsh(
                seed=42,
                tasks_per_cell=1,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=True,
                transport=fake_transport,
                transport_label="fake",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            task_runs = json.loads((result.artifact_path / "task_runs.json").read_text())
            combined_artifacts = "\n".join(
                [
                    (result.artifact_path / "metrics.json").read_text(),
                    (result.artifact_path / "task_runs.json").read_text(),
                    (result.artifact_path / "result_card.md").read_text(),
                    (result.artifact_path / "ledger.jsonl").read_text(),
                    (result.artifact_path / "replay" / "contexts.json").read_text(),
                ]
            )

        self.assertEqual(metrics["run_status"], "adapter_pilot_executed_fake_transport")
        self.assertEqual(metrics["cell_count"], 24)
        self.assertEqual(metrics["task_run_count"], 24)
        self.assertEqual(metrics["adapter_call_count"], 24)
        self.assertEqual(metrics["candidate_patch_present_count"], 24)
        self.assertEqual(metrics["hidden_verifier_pass_count"], 24)
        self.assertEqual(metrics["hidden_verifier_pass_rate"], 1.0)
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertEqual(metrics["transport_label"], "fake")
        self.assertEqual(metrics["adapter_usage_total_tokens"], 24 * 12)
        self.assertEqual(len(captured_requests), 24)
        self.assertEqual(captured_requests[0]["body"]["model"], "test/model")
        self.assertIn("Bearer dummy-secret-value", captured_requests[0]["headers"]["Authorization"])
        self.assertEqual({row["panel_type"] for row in task_runs["runs"]}, {"correlated_shared_context", "partitioned_disjoint_shards"})
        self.assertEqual({row["workspace_arm"] for row in task_runs["runs"]}, {"abundant", "random", "scarce_naive_topk", "scarce_protected"})
        self.assertEqual({row["seed_condition"] for row in task_runs["runs"]}, {"correct_minority", "incorrect_minority", "none"})
        self.assertTrue(all(row["candidate_patch"] == "x + 2" for row in task_runs["runs"]))
        self.assertTrue(all(row["candidate_patch_parse_status"] == "parsed" for row in task_runs["runs"]))
        self.assertTrue(all(row["hidden_verifier_passed"] for row in task_runs["runs"]))
        self.assertTrue(all(row["hidden_verifier_total"] == 3 for row in task_runs["runs"]))
        self.assertNotIn("dummy-secret-value", combined_artifacts)
        self.assertIn('"kind": "live_dsh_task_result"', combined_artifacts)
        self.assertIn('"kind": "live_dsh_verification"', combined_artifacts)
        self.assertIn("fake transport", combined_artifacts)

    def test_live_dsh_fake_transport_records_patch_parse_failures(self):
        from broadcast_alpha.live_dsh import run_live_dsh

        def fake_transport(_request):
            return {
                "id": "chatcmpl_fake_bad_patch",
                "choices": [{"message": {"content": "plain text without json patch"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
            }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\nOPENROUTER_MODEL=test/model\n")
            result = run_live_dsh(
                seed=42,
                tasks_per_cell=1,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=True,
                transport=fake_transport,
                transport_label="fake",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            task_runs = json.loads((result.artifact_path / "task_runs.json").read_text())

        self.assertEqual(metrics["candidate_patch_present_count"], 0)
        self.assertEqual(metrics["candidate_patch_parse_failure_count"], 24)
        self.assertEqual(metrics["hidden_verifier_pass_count"], 0)
        self.assertEqual(metrics["hidden_verifier_pass_rate"], 0.0)
        self.assertTrue(all(row["candidate_patch_parse_status"] == "missing_patch" for row in task_runs["runs"]))
        self.assertTrue(all(row["hidden_verifier_passed"] is False for row in task_runs["runs"]))

    def test_cli_run_live_dsh_default_creates_blocked_replayable_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-live-dsh",
                    "--seed",
                    "42",
                    "--tasks-per-cell",
                    "1",
                    "--artifact-root",
                    tmp,
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                env=_without_openrouter_env(),
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])
            metrics = json.loads((artifact_path / "metrics.json").read_text())

            self.assertEqual(metrics["run_status"], "blocked_no_live_execution")
            self.assertTrue((artifact_path / "task_runs.json").exists())

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
            self.assertIn("Live DSH pilot blocked", replay.stdout)

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

    def test_build_report_summarizes_required_rails(self):
        from broadcast_alpha.experiments import run_dsh, run_rqgm, run_synthetic
        from broadcast_alpha.jlens import run_jlens_gate
        from broadcast_alpha.live_dsh import run_live_dsh
        from broadcast_alpha.live_gate import run_live_gate
        from broadcast_alpha.reporting import build_result_report

        with tempfile.TemporaryDirectory() as tmp:
            artifact_root = Path(tmp)
            run_synthetic(seed=42, artifact_root=artifact_root)
            run_dsh(
                prereg_path=APP_ROOT / "prereg" / "PREREG_DSH-01.md",
                seed=42,
                tasks_per_cell=30,
                artifact_root=artifact_root,
            )
            run_rqgm(
                prereg_path=APP_ROOT / "prereg" / "PREREG_EPOCH-01.md",
                seed=42,
                epochs=5,
                artifact_root=artifact_root,
            )
            run_jlens_gate(seed=42, artifact_root=artifact_root)
            run_live_gate(seed=42, artifact_root=artifact_root, env={})
            run_live_dsh(seed=42, artifact_root=artifact_root, env={})
            result = build_result_report(artifact_root=artifact_root, output_dir=artifact_root / "final_report_seed_42")
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            result_table = json.loads((result.artifact_path / "result_table.json").read_text())
            claim_matrix = json.loads((result.artifact_path / "claim_matrix.json").read_text())
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(metrics["run_id"], "final_report_seed_42")
        self.assertEqual(metrics["glassgate_lift"], 0.4)
        self.assertEqual(metrics["seed_detectability_auc"], 0.5)
        self.assertEqual(metrics["seed_adversarial_auc"], 0.5)
        self.assertFalse(metrics["seed_camouflage_failed"])
        self.assertEqual(metrics["epoch_count"], 5)
        self.assertEqual(metrics["jlens_rail_status"], "frozen")
        self.assertEqual(metrics["live_model_rail_status"], "unavailable")
        self.assertFalse(metrics["live_adapter_call_performed"])
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertEqual(metrics["live_dsh_run_status"], "blocked_no_live_execution")
        self.assertEqual(metrics["live_dsh_adapter_call_count"], 0)
        self.assertEqual(metrics["live_dsh_hidden_verifier_pass_count"], 0)
        self.assertEqual(metrics["live_dsh_hidden_verifier_pass_rate"], 0.0)
        self.assertTrue(metrics["all_source_ledgers_verified"])
        self.assertEqual(metrics["report_status"], "complete_with_deferred_jlens")
        self.assertEqual(
            {row["section"] for row in result_table["rows"]},
            {"macro_dsh", "seed_detectability", "rqgm_epoch", "jlens_gate", "live_model_gate", "live_dsh_pilot"},
        )
        self.assertTrue(all(row["ledger_verified"] for row in result_table["rows"]))
        self.assertTrue(all(claim["evidence_path"] for claim in claim_matrix["claims"]))
        self.assertIn("GLASSGATE_LIFT", result_card)
        self.assertIn("Adversarial token AUC", result_card)
        self.assertIn("J-lens rail frozen", result_card)
        self.assertIn("Live model rail", result_card)

    def test_cli_build_report_creates_replayable_report_artifact(self):
        from broadcast_alpha.experiments import run_dsh, run_rqgm, run_synthetic
        from broadcast_alpha.jlens import run_jlens_gate
        from broadcast_alpha.live_dsh import run_live_dsh
        from broadcast_alpha.live_gate import run_live_gate

        with tempfile.TemporaryDirectory() as tmp:
            artifact_root = Path(tmp)
            run_synthetic(seed=42, artifact_root=artifact_root)
            run_dsh(
                prereg_path=APP_ROOT / "prereg" / "PREREG_DSH-01.md",
                seed=42,
                tasks_per_cell=30,
                artifact_root=artifact_root,
            )
            run_rqgm(
                prereg_path=APP_ROOT / "prereg" / "PREREG_EPOCH-01.md",
                seed=42,
                epochs=5,
                artifact_root=artifact_root,
            )
            run_jlens_gate(seed=42, artifact_root=artifact_root)
            run_live_gate(seed=42, artifact_root=artifact_root, env={})
            run_live_dsh(seed=42, artifact_root=artifact_root, env={})
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "build-report",
                    "--artifact-root",
                    tmp,
                    "--output",
                    str(artifact_root / "final_report_seed_42"),
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                env=_without_openrouter_env(),
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])
            metrics = json.loads((artifact_path / "metrics.json").read_text())

            self.assertTrue((artifact_path / "result_table.md").exists())
            self.assertTrue((artifact_path / "claim_matrix.json").exists())
            self.assertEqual(metrics["report_status"], "complete_with_deferred_jlens")
            self.assertEqual(metrics["live_model_rail_status"], "unavailable")
            self.assertEqual(metrics["live_dsh_run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_dsh_hidden_verifier_pass_rate"], 0.0)

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
            self.assertIn("final report", replay.stdout)

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

    def test_run_all_builds_self_contained_unattended_bundle(self):
        from broadcast_alpha.orchestrator import run_all

        with tempfile.TemporaryDirectory() as tmp:
            result = run_all(
                seed=42,
                tasks_per_cell=30,
                epochs=5,
                prereg_dir=APP_ROOT / "prereg",
                artifact_root=Path(tmp),
                live_env={},
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            manifest = json.loads((result.artifact_path / "manifest.json").read_text())
            final_metrics = json.loads((result.artifact_path / "final_report" / "metrics.json").read_text())
            self.assertEqual(result.run_id, "run_all_seed_42")
            self.assertEqual(metrics["run_status"], "complete_with_deferred_jlens")
            self.assertEqual(metrics["glassgate_lift"], 0.4)
            self.assertEqual(metrics["seed_adversarial_auc"], 0.5)
            self.assertEqual(metrics["jlens_rail_status"], "frozen")
            self.assertEqual(metrics["live_model_rail_status"], "unavailable")
            self.assertFalse(metrics["live_adapter_call_performed"])
            self.assertFalse(metrics["live_model_run_performed"])
            self.assertEqual(metrics["live_dsh_run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_dsh_adapter_call_count"], 0)
            self.assertEqual(metrics["live_dsh_hidden_verifier_pass_count"], 0)
            self.assertEqual(metrics["live_dsh_hidden_verifier_pass_rate"], 0.0)
            self.assertTrue(metrics["all_child_ledgers_verified"])
            self.assertEqual(final_metrics["report_status"], "complete_with_deferred_jlens")
            self.assertEqual(
                set(manifest["child_artifacts"]),
                {"synthetic", "dsh", "rqgm", "jlens_gate", "live_model_gate", "live_dsh_pilot", "final_report"},
            )
            self.assertTrue((result.artifact_path / "source_artifacts" / "dsh_seed_42" / "seed_audit.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "live_gate_seed_42" / "provider_status.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "live_dsh_seed_42" / "task_runs.json").exists())
            self.assertTrue((result.artifact_path / "final_report" / "claim_matrix.json").exists())

    def test_cli_run_all_creates_replayable_unattended_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-all",
                    "--seed",
                    "42",
                    "--tasks-per-cell",
                    "30",
                    "--epochs",
                    "5",
                    "--prereg-dir",
                    "prereg",
                    "--artifact-root",
                    tmp,
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                env=_without_openrouter_env(),
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])
            metrics = json.loads((artifact_path / "metrics.json").read_text())

            self.assertEqual(metrics["run_status"], "complete_with_deferred_jlens")
            self.assertEqual(metrics["live_model_rail_status"], "unavailable")
            self.assertEqual(metrics["live_dsh_run_status"], "blocked_no_live_execution")
            self.assertTrue((artifact_path / "final_report" / "result_table.md").exists())

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
            self.assertIn("unattended bundle", replay.stdout)

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

    def test_run_dsh_records_seed_detectability_audit(self):
        from broadcast_alpha.experiments import run_dsh

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dsh(
                prereg_path=APP_ROOT / "prereg" / "PREREG_DSH-01.md",
                seed=42,
                tasks_per_cell=30,
                artifact_root=Path(tmp),
            )
            task_runs = json.loads((result.artifact_path / "task_runs.json").read_text())
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            seed_audit = json.loads((result.artifact_path / "seed_audit.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()
            result_card = (result.artifact_path / "result_card.md").read_text()

        selected_ids = [row["selected_candidate_id"] for row in task_runs["runs"]]
        self.assertFalse(any("correct_minority" in selected_id for selected_id in selected_ids))
        self.assertFalse(any("incorrect_minority" in selected_id for selected_id in selected_ids))
        self.assertFalse(any("codebug_" in selected_id for selected_id in selected_ids))
        self.assertEqual(metrics["seed_audit_path"], str(result.artifact_path / "seed_audit.json"))
        self.assertEqual(metrics["seed_detectability_auc"], seed_audit["auc"])
        self.assertFalse(metrics["seed_camouflage_failed"])
        self.assertTrue(seed_audit["camouflage_passed"])
        self.assertEqual(seed_audit["auditor"], "marker_and_adversarial_token_auc_v1")
        self.assertEqual(seed_audit["public_feature_fields"], ["selected_candidate_id"])
        self.assertEqual(seed_audit["marker_auc"], 0.5)
        self.assertEqual(seed_audit["adversarial_auc"], 0.5)
        self.assertFalse(seed_audit["adversarial_camouflage_failed"])
        self.assertGreater(seed_audit["positive_count"], 0)
        self.assertGreater(seed_audit["negative_count"], 0)
        self.assertEqual(seed_audit["leak_markers_found"], [])
        self.assertIn('"kind": "seed_detectability_audit"', ledger)
        self.assertIn("Seed detectability audit", result_card)

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
