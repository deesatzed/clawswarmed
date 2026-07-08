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


def _fake_jlens_smoke_runner(runtime_python, source_repo, external_artifact_path, timeout_seconds):
    return {
        "smoke_status": "passed",
        "model_id": "reference_tiny_decoder",
        "model_source": "local_reference",
        "model_license": "Apache-2.0",
        "python_version": "test-python",
        "torch_version": "test-torch",
        "numpy_version": "test-numpy",
        "transformers_version": "test-transformers",
        "jlens_file": str(source_repo / "jlens" / "__init__.py"),
        "prompt_count": 2,
        "n_prompts": 2,
        "d_model": 8,
        "source_layers": [0, 1, 2],
        "lens_path": str(external_artifact_path / "lens.pt"),
        "input_token_count": 6,
        "lens_layers_returned": [0, 2],
        "gradient_access_confirmed": True,
        "layer_activation_access_confirmed": True,
    }


def _fake_jlens_hf_smoke_runner(runtime_python, source_repo, external_artifact_path, model_id, timeout_seconds):
    return {
        "smoke_status": "passed",
        "model_id": model_id,
        "model_source": "huggingface",
        "model_license": "unknown_not_declared",
        "model_revision": "test-revision",
        "model_type": "gpt2",
        "tokenizer_class": "GPT2Tokenizer",
        "hf_model_class": "GPT2LMHeadModel",
        "layout": "Layout(path='transformer')",
        "n_layers": 5,
        "d_model": 32,
        "vocab_size": 1000,
        "python_version": "test-python",
        "torch_version": "test-torch",
        "numpy_version": "test-numpy",
        "transformers_version": "test-transformers",
        "jlens_file": str(source_repo / "jlens" / "__init__.py"),
        "prompt_count": 2,
        "n_prompts": 2,
        "source_layers": [0, 1, 2, 3],
        "lens_path": str(external_artifact_path / "hf_lens.pt"),
        "input_token_count": 34,
        "lens_layers_returned": [0, 2, 3],
        "model_logits_shape": [1, 1000],
        "selected_label_check": {
            " A": {"token_ids": [240], "single_token": True, "decoded": " A"},
            " B": {"token_ids": [265], "single_token": True, "decoded": " B"},
        },
        "critical_label_check": {
            "yes": {"token_ids": [89, 216], "single_token": False, "decoded": "yes"},
        },
        "selected_labels_all_single_token": True,
        "critical_labels_all_single_token": False,
        "gradient_access_confirmed": True,
        "layer_activation_access_confirmed": True,
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

    def test_ledger_stress_creates_mixed_10k_receipt_artifact(self):
        from broadcast_alpha.ledger import Ledger
        from broadcast_alpha.ledger_stress import run_ledger_stress

        with tempfile.TemporaryDirectory() as tmp:
            result = run_ledger_stress(seed=42, receipt_count=10_000, artifact_root=Path(tmp))
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            kind_counts = json.loads((result.artifact_path / "receipt_kind_counts.json").read_text())
            ledger = Ledger.from_jsonl(result.artifact_path / "ledger.jsonl")
            replay_context = (result.artifact_path / "replay" / "contexts.json").read_text()

        self.assertEqual(result.run_id, "ledger_stress_seed_42")
        self.assertEqual(metrics["synthetic_receipt_count"], 10_000)
        self.assertEqual(metrics["total_receipt_count"], 10_001)
        self.assertGreaterEqual(metrics["mixed_kind_count"], 6)
        self.assertTrue(metrics["pre_metrics_chain_verified"])
        self.assertTrue(metrics["ledger_verified"])
        self.assertTrue(metrics["tamper_detection_passed"])
        self.assertEqual(sum(kind_counts.values()), 10_000)
        self.assertTrue(all(count > 0 for count in kind_counts.values()))
        self.assertTrue(ledger.verify_chain())
        self.assertIn("10,000 mixed synthetic receipts", replay_context)

    def test_cli_run_ledger_stress_creates_replayable_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-ledger-stress",
                    "--seed",
                    "42",
                    "--receipt-count",
                    "10000",
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

            self.assertEqual(payload["run_id"], "ledger_stress_seed_42")
            self.assertEqual(metrics["synthetic_receipt_count"], 10_000)
            self.assertTrue(metrics["tamper_detection_passed"])

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
            self.assertIn("tamper check passed", replay.stdout)

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

    def test_jlens_gate_freezes_after_exact_source_until_white_box_model(self):
        from broadcast_alpha.jlens import run_jlens_gate

        with tempfile.TemporaryDirectory() as tmp:
            result = run_jlens_gate(seed=42, artifact_root=Path(tmp))
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            sources = json.loads((result.artifact_path / "sources.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(metrics["rail_status"], "frozen")
        self.assertTrue(metrics["required_exact_source_found"])
        self.assertFalse(metrics["white_box_model_available"])
        self.assertFalse(metrics["real_probe_runnable"])
        self.assertEqual(metrics["failure_ledger_entry_id"], "JLENS-FREEZE-001")
        exact_sources = sources["verified_exact_sources"]
        self.assertEqual(exact_sources[0]["url"], "https://github.com/anthropics/jacobian-lens")
        self.assertEqual(exact_sources[0]["license"], "Apache-2.0")
        self.assertEqual(exact_sources[0]["commit_sha"], "581d398613e5602a5af361e1c34d3a92ea82ba8e")
        self.assertEqual(exact_sources[0]["date_accessed"], "2026-07-08")
        self.assertIn("source_verified_runtime_unavailable", metrics["reason_codes"])
        self.assertNotIn("exact_jlens_source_not_verified", metrics["reason_codes"])
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

    def test_jlens_vignette_packet_is_checked_in_and_non_proof(self):
        packet = json.loads(Path("prereg/jlens_vignette_packet_01.json").read_text())

        self.assertEqual(packet["artifact_type"], "jlens_vignette_packet")
        self.assertTrue(packet["not_formal_proof"])
        self.assertGreaterEqual(len(packet["paired_vignettes"]), 2)
        for pair in packet["paired_vignettes"]:
            self.assertIn("outcome_withheld", pair)
            self.assertIn("outcome_revealed", pair)
            self.assertIn("expected_verdict_labels", pair)
            self.assertGreaterEqual(len(pair["expected_verdict_labels"]), 2)
            for label in pair["expected_verdict_labels"]:
                self.assertEqual(label, label.strip())
                self.assertEqual(len(label.split()), 1)

    def test_jlens_manual_sanity_template_blocks_formal_claim(self):
        template = Path("docs/JLENS_MANUAL_SANITY_TEMPLATE.md").read_text()

        self.assertIn("Neuronpedia", template)
        self.assertIn("not formal proof", template.lower())
        self.assertIn("white-box", template.lower())

    def test_jlens_gate_single_token_label_manifest(self):
        from broadcast_alpha.jlens import verify_single_token_labels

        labels = ["yes", "no", "admit", "reject", "pass", "fail"]

        self.assertEqual(
            verify_single_token_labels(labels),
            {label: True for label in labels},
        )
        with self.assertRaises(ValueError):
            verify_single_token_labels(["yes", "not sure"])

    def test_prepare_jlens_probe_rejects_black_box_providers(self):
        from broadcast_alpha.jlens_runtime import prepare_jlens_probe

        with tempfile.TemporaryDirectory() as tmp:
            result = prepare_jlens_probe(
                seed=42,
                artifact_root=Path(tmp),
                model_id="openai/gpt-4.1",
                model_source="openrouter",
                require_jacobian_lens=False,
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            model_manifest = json.loads((result.artifact_path / "model_manifest.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()

        self.assertEqual(metrics["readiness_status"], "blocked_black_box_provider")
        self.assertFalse(metrics["white_box_model_available"])
        self.assertFalse(metrics["gradient_access_confirmed"])
        self.assertFalse(metrics["real_probe_runnable"])
        self.assertIn("black_box_provider_rejected", metrics["reason_codes"])
        self.assertTrue(model_manifest["black_box_provider_rejected"])
        self.assertIn('"kind": "jlens_runtime_readiness"', ledger)

    def test_prepare_jlens_probe_records_missing_runtime_dependencies(self):
        from broadcast_alpha.jlens_runtime import prepare_jlens_probe

        with tempfile.TemporaryDirectory() as tmp:
            result = prepare_jlens_probe(
                seed=42,
                artifact_root=Path(tmp),
                model_id="hf-internal-testing/tiny-random-gpt2",
                model_source="huggingface",
                require_jacobian_lens=True,
                module_probe={
                    "torch": False,
                    "transformers": False,
                    "jlens": False,
                },
                tokenizer_single_token={
                    "yes": True,
                    "no": True,
                    "admit": False,
                    "reject": False,
                    "pass": True,
                    "fail": True,
                },
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            model_manifest = json.loads((result.artifact_path / "model_manifest.json").read_text())
            labels = json.loads((result.artifact_path / "tokenizer_label_check.json").read_text())
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(metrics["readiness_status"], "blocked_missing_dependencies")
        self.assertEqual(metrics["model_source"], "huggingface")
        self.assertFalse(metrics["white_box_model_available"])
        self.assertFalse(metrics["gradient_access_confirmed"])
        self.assertFalse(metrics["real_probe_runnable"])
        self.assertIn("torch_missing", metrics["reason_codes"])
        self.assertIn("transformers_missing", metrics["reason_codes"])
        self.assertIn("jacobian_lens_reference_missing", metrics["reason_codes"])
        self.assertEqual(labels["labels"]["admit"]["single_token"], False)
        self.assertEqual(model_manifest["runtime_requirements"]["requires_gradient_access"], True)
        self.assertIn("not a real J-lens probe", result_card)

    def test_cli_prepare_jlens_probe_creates_readiness_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "prepare-jlens-probe",
                    "--seed",
                    "42",
                    "--artifact-root",
                    tmp,
                    "--model-id",
                    "hf-internal-testing/tiny-random-gpt2",
                    "--model-source",
                    "huggingface",
                ],
                cwd=APP_ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            payload = json.loads(result.stdout)
            artifact_path = Path(payload["artifact_path"])

            self.assertTrue((artifact_path / "metrics.json").exists())
            self.assertTrue((artifact_path / "model_manifest.json").exists())
            self.assertTrue((artifact_path / "tokenizer_label_check.json").exists())

    def test_run_jlens_smoke_records_real_fit_apply_payload(self):
        from broadcast_alpha.jlens_smoke import run_jlens_smoke

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_repo = tmp_path / "jacobian-lens"
            runtime_python = tmp_path / "python"
            source_repo.mkdir()
            runtime_python.write_text("# fake runtime\n")
            result = run_jlens_smoke(
                seed=42,
                artifact_root=tmp_path,
                runtime_python=runtime_python,
                source_repo=source_repo,
                runner=_fake_jlens_smoke_runner,
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            smoke_payload = json.loads((result.artifact_path / "smoke_payload.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()

        self.assertEqual(metrics["smoke_status"], "passed")
        self.assertTrue(metrics["gradient_access_confirmed"])
        self.assertTrue(metrics["layer_activation_access_confirmed"])
        self.assertFalse(metrics["causal_intervention_performed"])
        self.assertTrue(metrics["not_sufficient_for_JLENS_PROVED"])
        self.assertEqual(smoke_payload["source_layers"], [0, 1, 2])
        self.assertIn('"kind": "jlens_smoke_result"', ledger)

    def test_jlens_smoke_blocks_missing_runtime(self):
        from broadcast_alpha.jlens_smoke import run_jlens_smoke

        with tempfile.TemporaryDirectory() as tmp:
            result = run_jlens_smoke(
                seed=42,
                artifact_root=Path(tmp),
                runtime_python=Path(tmp) / "missing-python",
                source_repo=Path(tmp) / "missing-repo",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())

        self.assertEqual(metrics["smoke_status"], "blocked_missing_runtime")
        self.assertFalse(metrics["real_jlens_fit_apply_smoke"])
        self.assertIn("runtime_python_missing", metrics["reason_codes"])

    def test_run_jlens_hf_smoke_records_tokenizer_and_model_manifest(self):
        from broadcast_alpha.jlens_hf_smoke import run_jlens_hf_smoke

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_repo = tmp_path / "jacobian-lens"
            runtime_python = tmp_path / "python"
            source_repo.mkdir()
            runtime_python.write_text("# fake runtime\n")
            result = run_jlens_hf_smoke(
                seed=42,
                artifact_root=tmp_path,
                runtime_python=runtime_python,
                source_repo=source_repo,
                model_id="hf-internal-testing/tiny-random-gpt2",
                runner=_fake_jlens_hf_smoke_runner,
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            manifest = json.loads((result.artifact_path / "model_manifest.json").read_text())
            labels = json.loads((result.artifact_path / "tokenizer_label_check.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()

        self.assertEqual(metrics["smoke_status"], "passed")
        self.assertTrue(metrics["real_hf_jlens_fit_apply_smoke"])
        self.assertTrue(metrics["selected_labels_all_single_token"])
        self.assertFalse(metrics["critical_labels_all_single_token"])
        self.assertTrue(metrics["gradient_access_confirmed"])
        self.assertFalse(metrics["causal_intervention_performed"])
        self.assertTrue(metrics["not_sufficient_for_JLENS_PROVED"])
        self.assertEqual(manifest["model_revision"], "test-revision")
        self.assertEqual(labels["selected_label_check"][" A"]["single_token"], True)
        self.assertIn('"kind": "jlens_hf_smoke_result"', ledger)

    def test_jlens_hf_smoke_blocks_missing_runtime(self):
        from broadcast_alpha.jlens_hf_smoke import run_jlens_hf_smoke

        with tempfile.TemporaryDirectory() as tmp:
            result = run_jlens_hf_smoke(
                seed=42,
                artifact_root=Path(tmp),
                runtime_python=Path(tmp) / "missing-python",
                source_repo=Path(tmp) / "missing-repo",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())

        self.assertEqual(metrics["smoke_status"], "blocked_missing_runtime")
        self.assertFalse(metrics["real_hf_jlens_fit_apply_smoke"])
        self.assertIn("runtime_python_missing", metrics["reason_codes"])

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

    def test_live_dsh_prereg_file_declares_no_default_spend_and_no_lift_claim(self):
        prereg = (APP_ROOT / "prereg" / "PREREG_LIVE-01.md").read_text()

        self.assertIn("run-live-dsh", prereg)
        self.assertIn("blocked_no_live_execution", prereg)
        self.assertIn("--execute-live", prereg)
        self.assertIn("--authorize-api-spend", prereg)
        self.assertIn("No GLASSGATE_LIFT claim", prereg)

    def test_live_dsh_records_preregistration_metadata(self):
        from broadcast_alpha.live_dsh import run_live_dsh

        prereg_path = APP_ROOT / "prereg" / "PREREG_LIVE-01.md"

        with tempfile.TemporaryDirectory() as tmp:
            result = run_live_dsh(
                seed=42,
                tasks_per_cell=1,
                artifact_root=Path(tmp),
                env={},
                prereg_path=prereg_path,
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            ledger = (result.artifact_path / "ledger.jsonl").read_text()
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(metrics["prereg_id"], "PREREG_LIVE-01")
        self.assertEqual(metrics["prereg_path"], str(prereg_path))
        self.assertTrue(metrics["prereg_exists"])
        self.assertIn('"prereg_id": "PREREG_LIVE-01"', ledger)
        self.assertIn("PREREG_LIVE-01", result_card)

    def test_live_dsh_blocks_ready_transport_when_prereg_is_missing(self):
        from broadcast_alpha.live_dsh import run_live_dsh

        transport_calls = []

        def fake_transport(request):
            transport_calls.append(request)
            return {"choices": [{"message": {"content": "{\"patch\": \"x + 2\"}"}}]}

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            missing_prereg = tmp_path / "missing" / "PREREG_LIVE-01.md"
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
                prereg_path=missing_prereg,
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())

        self.assertEqual(metrics["run_status"], "blocked_no_live_execution")
        self.assertFalse(metrics["prereg_exists"])
        self.assertIn("missing_preregistration_file", metrics["reason_codes"])
        self.assertEqual(metrics["adapter_call_count"], 0)
        self.assertEqual(transport_calls, [])

    def test_live_smoke_default_blocks_without_adapter_execution(self):
        from broadcast_alpha.live_dsh import run_live_smoke

        with tempfile.TemporaryDirectory() as tmp:
            result = run_live_smoke(
                seed=42,
                artifact_root=Path(tmp),
                env={},
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            task_runs = json.loads((result.artifact_path / "task_runs.json").read_text())
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(result.run_id, "live_smoke_seed_42")
        self.assertEqual(metrics["run_mode"], "live_smoke")
        self.assertEqual(metrics["run_status"], "blocked_no_live_execution")
        self.assertEqual(metrics["available_cell_count"], 24)
        self.assertEqual(metrics["cell_limit"], 1)
        self.assertEqual(metrics["cell_count"], 1)
        self.assertEqual(metrics["planned_task_runs"], 1)
        self.assertEqual(metrics["task_run_count"], 0)
        self.assertEqual(metrics["adapter_call_count"], 0)
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertNotIn("glassgate_lift", metrics)
        self.assertEqual(task_runs["runs"], [])
        self.assertIn("Live smoke blocked", result_card)

    def test_live_smoke_fake_transport_executes_one_verifier_backed_call(self):
        from broadcast_alpha.live_dsh import run_live_smoke

        captured_requests = []

        def fake_transport(request):
            captured_requests.append(request)
            return {
                "id": "chatcmpl_fake_smoke",
                "choices": [{"message": {"content": "{\"patch\": \"x + 2\", \"rationale\": \"repair add\"}"}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 3, "total_tokens": 12},
            }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\nOPENROUTER_MODEL=test/model\n")
            result = run_live_smoke(
                seed=42,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=True,
                transport=fake_transport,
                transport_label="fake",
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            task_runs = json.loads((result.artifact_path / "task_runs.json").read_text())
            combined_artifacts = "\n".join(
                [
                    (result.artifact_path / "metrics.json").read_text(),
                    (result.artifact_path / "task_runs.json").read_text(),
                    (result.artifact_path / "result_card.md").read_text(),
                    (result.artifact_path / "ledger.jsonl").read_text(),
                ]
            )

        self.assertEqual(metrics["run_status"], "adapter_pilot_executed_fake_transport")
        self.assertEqual(metrics["run_mode"], "live_smoke")
        self.assertEqual(metrics["cell_count"], 1)
        self.assertEqual(metrics["planned_task_runs"], 1)
        self.assertEqual(metrics["task_run_count"], 1)
        self.assertEqual(metrics["adapter_call_count"], 1)
        self.assertEqual(metrics["candidate_patch_present_count"], 1)
        self.assertEqual(metrics["hidden_verifier_pass_count"], 1)
        self.assertEqual(metrics["hidden_verifier_pass_rate"], 1.0)
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertEqual(len(captured_requests), 1)
        self.assertEqual(captured_requests[0]["metadata"]["panel_type"], "correlated_shared_context")
        self.assertEqual(captured_requests[0]["metadata"]["workspace_arm"], "abundant")
        self.assertEqual(captured_requests[0]["metadata"]["seed_condition"], "correct_minority")
        self.assertEqual(len(task_runs["runs"]), 1)
        self.assertEqual(task_runs["runs"][0]["candidate_patch"], "x + 2")
        self.assertTrue(task_runs["runs"][0]["hidden_verifier_passed"])
        self.assertNotIn("dummy-secret-value", combined_artifacts)

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
            self.assertEqual(metrics["prereg_id"], "PREREG_LIVE-01")
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

    def test_cli_run_live_smoke_default_creates_blocked_replayable_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-live-smoke",
                    "--seed",
                    "42",
                    "--artifact-root",
                    tmp,
                    "--prereg",
                    "prereg/PREREG_LIVE-01.md",
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

            self.assertEqual(payload["run_id"], "live_smoke_seed_42")
            self.assertEqual(metrics["run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["planned_task_runs"], 1)
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
            self.assertIn("Live smoke blocked", replay.stdout)

    def test_prepare_live_smoke_preview_redacts_secret_and_hidden_tests(self):
        from broadcast_alpha.live_readiness import prepare_live_smoke
        from broadcast_alpha.task_bank import load_codebug_tasks

        first_task = load_codebug_tasks()[0]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\nOPENROUTER_MODEL=test/model\n")
            result = prepare_live_smoke(
                seed=42,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            request_preview = json.loads((result.artifact_path / "request_preview.json").read_text())
            gate_checklist = json.loads((result.artifact_path / "gate_checklist.json").read_text())
            combined_artifacts = "\n".join(
                [
                    (result.artifact_path / "metrics.json").read_text(),
                    (result.artifact_path / "request_preview.json").read_text(),
                    (result.artifact_path / "gate_checklist.json").read_text(),
                    (result.artifact_path / "result_card.md").read_text(),
                    (result.artifact_path / "ledger.jsonl").read_text(),
                ]
            )

        self.assertEqual(result.run_id, "live_readiness_seed_42")
        self.assertEqual(metrics["readiness_status"], "ready_pending_authorization")
        self.assertEqual(metrics["adapter_call_count"], 0)
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertFalse(metrics["secret_values_recorded"])
        self.assertTrue(metrics["openrouter_api_key_present"])
        self.assertTrue(metrics["model_configured"])
        self.assertEqual(request_preview["headers"]["Authorization"], "REDACTED")
        self.assertEqual(request_preview["body"]["model"], "test/model")
        self.assertEqual(request_preview["metadata"]["workspace_arm"], "abundant")
        self.assertEqual(request_preview["metadata"]["seed_condition"], "correct_minority")
        self.assertEqual(request_preview["task"]["hidden_test_count"], 3)
        self.assertNotIn("hidden_tests", request_preview["task"])
        self.assertNotIn("correct_patch", request_preview["task"])
        self.assertNotIn("incorrect_patch", request_preview["task"])
        self.assertNotIn("dummy-secret-value", combined_artifacts)
        self.assertNotIn(first_task.correct_patch, combined_artifacts)
        self.assertNotIn(first_task.incorrect_patch, combined_artifacts)
        self.assertIn("--execute-live", gate_checklist["next_command"])

    def test_cli_prepare_live_smoke_creates_replayable_readiness_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "prepare-live-smoke",
                    "--seed",
                    "42",
                    "--artifact-root",
                    tmp,
                    "--prereg",
                    "prereg/PREREG_LIVE-01.md",
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

            self.assertEqual(payload["run_id"], "live_readiness_seed_42")
            self.assertEqual(metrics["readiness_status"], "blocked_missing_configuration")
            self.assertEqual(metrics["adapter_call_count"], 0)
            self.assertTrue((artifact_path / "request_preview.json").exists())

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
            self.assertIn("live readiness", replay.stdout)

    def test_live_sequence_default_blocks_before_smoke_without_adapter_calls(self):
        from broadcast_alpha.live_sequence import run_live_sequence

        with tempfile.TemporaryDirectory() as tmp:
            result = run_live_sequence(
                seed=42,
                artifact_root=Path(tmp),
                env={},
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            manifest = json.loads((result.artifact_path / "manifest.json").read_text())
            result_card = (result.artifact_path / "result_card.md").read_text()

        self.assertEqual(result.run_id, "live_sequence_seed_42")
        self.assertEqual(metrics["sequence_status"], "blocked_before_smoke")
        self.assertEqual(metrics["adapter_call_count_total"], 0)
        self.assertEqual(metrics["smoke_run_status"], "blocked_no_live_execution")
        self.assertEqual(metrics["pilot_run_status"], "not_requested")
        self.assertFalse(metrics["pilot_promoted"])
        self.assertNotIn("glassgate_lift", metrics)
        self.assertIn("live_model_gate", manifest["child_artifacts"])
        self.assertIn("live_smoke", manifest["child_artifacts"])
        self.assertNotIn("live_dsh_pilot", manifest["child_artifacts"])
        self.assertIn("blocked before smoke", result_card)

    def test_live_sequence_fake_transport_runs_smoke_only_by_default(self):
        from broadcast_alpha.live_sequence import run_live_sequence

        captured_requests = []

        def fake_transport(request):
            captured_requests.append(request)
            return {
                "id": f"chatcmpl_fake_sequence_{len(captured_requests)}",
                "choices": [{"message": {"content": "{\"patch\": \"x + 2\"}"}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 3, "total_tokens": 12},
            }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\nOPENROUTER_MODEL=test/model\n")
            result = run_live_sequence(
                seed=42,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=True,
                transport=fake_transport,
                transport_label="fake",
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            manifest = json.loads((result.artifact_path / "manifest.json").read_text())
            combined_artifacts = "\n".join(
                [
                    (result.artifact_path / "metrics.json").read_text(),
                    (result.artifact_path / "manifest.json").read_text(),
                    (result.artifact_path / "ledger.jsonl").read_text(),
                ]
            )

        self.assertEqual(metrics["sequence_status"], "smoke_passed_pilot_not_requested")
        self.assertEqual(metrics["adapter_call_count_total"], 1)
        self.assertEqual(metrics["smoke_run_status"], "adapter_pilot_executed_fake_transport")
        self.assertEqual(metrics["smoke_hidden_verifier_pass_count"], 1)
        self.assertEqual(metrics["pilot_run_status"], "not_requested")
        self.assertFalse(metrics["pilot_promoted"])
        self.assertEqual(len(captured_requests), 1)
        self.assertIn("live_smoke", manifest["child_artifacts"])
        self.assertNotIn("live_dsh_pilot", manifest["child_artifacts"])
        self.assertNotIn("dummy-secret-value", combined_artifacts)

    def test_live_sequence_promotes_to_pilot_after_fake_smoke_pass(self):
        from broadcast_alpha.live_sequence import run_live_sequence

        captured_requests = []

        def fake_transport(request):
            captured_requests.append(request)
            return {
                "id": f"chatcmpl_fake_sequence_{len(captured_requests)}",
                "choices": [{"message": {"content": "{\"patch\": \"x + 2\"}"}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 3, "total_tokens": 12},
            }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text("OPENROUTER_API_KEY=dummy-secret-value\nOPENROUTER_MODEL=test/model\n")
            result = run_live_sequence(
                seed=42,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=True,
                include_dsh_pilot=True,
                transport=fake_transport,
                transport_label="fake",
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            manifest = json.loads((result.artifact_path / "manifest.json").read_text())

        self.assertEqual(metrics["sequence_status"], "pilot_executed_after_smoke_pass")
        self.assertTrue(metrics["pilot_promoted"])
        self.assertEqual(metrics["smoke_hidden_verifier_pass_count"], 1)
        self.assertEqual(metrics["pilot_run_status"], "adapter_pilot_executed_fake_transport")
        self.assertEqual(metrics["pilot_hidden_verifier_pass_count"], 24)
        self.assertEqual(metrics["adapter_call_count_total"], 25)
        self.assertEqual(len(captured_requests), 25)
        self.assertIn("live_dsh_pilot", manifest["child_artifacts"])

    def test_live_model_sweep_reads_numbered_models_and_runs_one_smoke_per_model(self):
        from broadcast_alpha.live_model_sweep import run_live_model_sweep

        captured_requests = []

        def fake_transport(request):
            captured_requests.append(request)
            return {
                "id": f"chatcmpl_fake_sweep_{len(captured_requests)}",
                "choices": [{"message": {"content": "{\"patch\": \"x + 2\"}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
            }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text(
                "OPENROUTER_API_KEY=dummy-secret-value\n"
                "OPENROUTER_MODEL_1=test/model-a\n"
                "OPENROUTER_MODEL_2=test/model-b\n"
            )
            result = run_live_model_sweep(
                seed=42,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=True,
                budget_usd=25.0,
                transport=fake_transport,
                transport_label="fake",
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            model_results = json.loads((result.artifact_path / "model_results.json").read_text())
            manifest = json.loads((result.artifact_path / "manifest.json").read_text())
            combined_artifacts = "\n".join(
                [
                    (result.artifact_path / "metrics.json").read_text(),
                    (result.artifact_path / "model_results.json").read_text(),
                    (result.artifact_path / "manifest.json").read_text(),
                    (result.artifact_path / "result_card.md").read_text(),
                    (result.artifact_path / "ledger.jsonl").read_text(),
                ]
            )

        self.assertEqual(result.run_id, "live_model_sweep_seed_42")
        self.assertEqual(metrics["sweep_status"], "sweep_executed")
        self.assertEqual(metrics["model_count"], 2)
        self.assertEqual(metrics["attempted_model_count"], 2)
        self.assertEqual(metrics["adapter_call_count_total"], 2)
        self.assertEqual(metrics["live_model_run_performed_count"], 0)
        self.assertEqual(metrics["budget_usd"], 25.0)
        self.assertEqual(metrics["transport_label"], "fake")
        self.assertEqual(len(captured_requests), 2)
        self.assertEqual([request["body"]["model"] for request in captured_requests], ["test/model-a", "test/model-b"])
        self.assertEqual([row["model_ref"] for row in model_results["models"]], ["test/model-a", "test/model-b"])
        self.assertTrue(all(row["hidden_verifier_pass_count"] == 1 for row in model_results["models"]))
        self.assertEqual(set(manifest["child_artifacts"]), {"model_1", "model_2"})
        self.assertNotIn("dummy-secret-value", combined_artifacts)

    def test_live_model_sweep_blocks_without_spend_authorization(self):
        from broadcast_alpha.live_model_sweep import run_live_model_sweep

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text(
                "OPENROUTER_API_KEY=dummy-secret-value\n"
                "OPENROUTER_MODEL_1=test/model-a\n"
            )
            result = run_live_model_sweep(
                seed=42,
                artifact_root=tmp_path,
                env_file=env_file,
                env={},
                budget_usd=25.0,
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            model_results = json.loads((result.artifact_path / "model_results.json").read_text())

        self.assertEqual(metrics["sweep_status"], "blocked_no_live_execution")
        self.assertEqual(metrics["model_count"], 1)
        self.assertEqual(metrics["attempted_model_count"], 0)
        self.assertEqual(metrics["adapter_call_count_total"], 0)
        self.assertEqual(model_results["models"], [])
        self.assertIn("api_spend_not_authorized", metrics["reason_codes"])

    def test_cli_run_live_model_sweep_creates_replayable_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env_file = tmp_path / "provider.env"
            env_file.write_text(
                "OPENROUTER_API_KEY=dummy-secret-value\n"
                "OPENROUTER_MODEL_1=test/model-a\n"
                "OPENROUTER_MODEL_2=test/model-b\n"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-live-model-sweep",
                    "--seed",
                    "42",
                    "--artifact-root",
                    str(tmp_path / "artifacts"),
                    "--env-file",
                    str(env_file),
                    "--budget-usd",
                    "25",
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

            self.assertEqual(payload["run_id"], "live_model_sweep_seed_42")
            self.assertEqual(metrics["sweep_status"], "blocked_no_live_execution")
            self.assertTrue((artifact_path / "model_results.json").exists())

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
            self.assertIn("live model sweep", replay.stdout)

    def test_cli_run_live_sequence_default_creates_blocked_replayable_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "run-live-sequence",
                    "--seed",
                    "42",
                    "--artifact-root",
                    tmp,
                    "--prereg",
                    "prereg/PREREG_LIVE-01.md",
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

            self.assertEqual(payload["run_id"], "live_sequence_seed_42")
            self.assertEqual(metrics["sequence_status"], "blocked_before_smoke")
            self.assertTrue((artifact_path / "manifest.json").exists())

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
            self.assertIn("live sequence blocked before smoke", replay.stdout)

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
        from broadcast_alpha.jlens_hf_smoke import run_jlens_hf_smoke
        from broadcast_alpha.jlens_runtime import prepare_jlens_probe
        from broadcast_alpha.jlens_smoke import run_jlens_smoke
        from broadcast_alpha.ledger_stress import run_ledger_stress
        from broadcast_alpha.live_dsh import run_live_dsh, run_live_smoke
        from broadcast_alpha.live_gate import run_live_gate
        from broadcast_alpha.live_sequence import run_live_sequence
        from broadcast_alpha.reporting import build_result_report

        with tempfile.TemporaryDirectory() as tmp:
            artifact_root = Path(tmp)
            run_ledger_stress(seed=42, receipt_count=10_000, artifact_root=artifact_root)
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
            prepare_jlens_probe(seed=42, artifact_root=artifact_root)
            smoke_repo = artifact_root / "fake-jlens-repo"
            smoke_python = artifact_root / "fake-python"
            smoke_repo.mkdir()
            smoke_python.write_text("# fake python\n")
            run_jlens_smoke(
                seed=42,
                artifact_root=artifact_root,
                runtime_python=smoke_python,
                source_repo=smoke_repo,
                runner=_fake_jlens_smoke_runner,
            )
            run_jlens_hf_smoke(
                seed=42,
                artifact_root=artifact_root,
                runtime_python=smoke_python,
                source_repo=smoke_repo,
                model_id="hf-internal-testing/tiny-random-gpt2",
                runner=_fake_jlens_hf_smoke_runner,
            )
            run_live_gate(seed=42, artifact_root=artifact_root, env={})
            run_live_smoke(
                seed=42,
                artifact_root=artifact_root,
                env={},
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            run_live_dsh(seed=42, artifact_root=artifact_root, env={})
            run_live_sequence(
                seed=42,
                artifact_root=artifact_root,
                env={},
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
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
        self.assertEqual(metrics["jlens_runtime_readiness_status"], "blocked_missing_dependencies")
        self.assertFalse(metrics["jlens_runtime_white_box_model_available"])
        self.assertFalse(metrics["jlens_runtime_gradient_access_confirmed"])
        self.assertFalse(metrics["jlens_runtime_real_probe_runnable"])
        self.assertIn("torch_missing", metrics["jlens_runtime_reason_codes"])
        self.assertEqual(metrics["jlens_smoke_status"], "passed")
        self.assertTrue(metrics["jlens_smoke_real_fit_apply"])
        self.assertTrue(metrics["jlens_smoke_not_sufficient_for_JLENS_PROVED"])
        self.assertEqual(metrics["jlens_hf_smoke_status"], "passed")
        self.assertTrue(metrics["jlens_hf_smoke_real_fit_apply"])
        self.assertTrue(metrics["jlens_hf_selected_labels_all_single_token"])
        self.assertFalse(metrics["jlens_hf_critical_labels_all_single_token"])
        self.assertTrue(metrics["jlens_hf_smoke_not_sufficient_for_JLENS_PROVED"])
        self.assertEqual(metrics["live_model_rail_status"], "unavailable")
        self.assertFalse(metrics["live_adapter_call_performed"])
        self.assertFalse(metrics["live_model_run_performed"])
        self.assertEqual(metrics["live_smoke_run_status"], "blocked_no_live_execution")
        self.assertEqual(metrics["live_smoke_adapter_call_count"], 0)
        self.assertEqual(metrics["live_smoke_hidden_verifier_pass_count"], 0)
        self.assertEqual(metrics["live_dsh_run_status"], "blocked_no_live_execution")
        self.assertEqual(metrics["live_dsh_adapter_call_count"], 0)
        self.assertEqual(metrics["live_dsh_prereg_id"], "PREREG_LIVE-01")
        self.assertEqual(metrics["live_dsh_hidden_verifier_pass_count"], 0)
        self.assertEqual(metrics["live_dsh_hidden_verifier_pass_rate"], 0.0)
        self.assertEqual(metrics["live_sequence_status"], "blocked_before_smoke")
        self.assertEqual(metrics["live_sequence_adapter_call_count_total"], 0)
        self.assertEqual(metrics["live_sequence_smoke_status"], "blocked_no_live_execution")
        self.assertEqual(metrics["live_sequence_pilot_status"], "not_requested")
        self.assertFalse(metrics["live_sequence_pilot_promoted"])
        self.assertTrue(metrics["live_sequence_all_child_ledgers_verified"])
        self.assertEqual(metrics["ledger_stress_synthetic_receipt_count"], 10_000)
        self.assertGreaterEqual(metrics["ledger_stress_mixed_kind_count"], 6)
        self.assertTrue(metrics["ledger_stress_tamper_detection_passed"])
        self.assertTrue(metrics["ledger_stress_ledger_verified"])
        self.assertEqual(metrics["verified_solve_rate"]["scarce_protected"], 0.761111)
        self.assertEqual(metrics["panel_correlation_rho"]["correlated_shared_context"], 0.82)
        self.assertEqual(metrics["candidate_ablation_rate"], 0.297222)
        self.assertIsNone(metrics["token_cost_per_solve"])
        self.assertTrue(metrics["all_source_ledgers_verified"])
        self.assertEqual(metrics["report_status"], "complete_with_deferred_jlens")
        self.assertEqual(
            {row["section"] for row in result_table["rows"]},
            {
                "ledger_stress",
                "macro_dsh",
                "seed_detectability",
                "rqgm_epoch",
                "jlens_gate",
                "jlens_runtime_readiness",
                "jlens_smoke",
                "jlens_hf_smoke",
                "live_model_gate",
                "live_smoke",
                "live_dsh_pilot",
                "live_sequence",
            },
        )
        self.assertTrue(all(row["ledger_verified"] for row in result_table["rows"]))
        self.assertTrue(all(claim["evidence_path"] for claim in claim_matrix["claims"]))
        self.assertTrue(any("live-provider sequence" in claim["claim"] for claim in claim_matrix["claims"]))
        self.assertTrue(any("10,000 mixed synthetic receipts" in claim["claim"] for claim in claim_matrix["claims"]))
        self.assertTrue(any("macro diagnostics" in claim["claim"] for claim in claim_matrix["claims"]))
        self.assertIn("GLASSGATE_LIFT", result_card)
        self.assertIn("10k ledger stress", result_card)
        self.assertIn("Macro diagnostics", result_card)
        self.assertIn("Candidate ablation rate", result_card)
        self.assertIn("Adversarial token AUC", result_card)
        self.assertIn("J-lens rail frozen", result_card)
        self.assertIn("Runtime readiness", result_card)
        self.assertIn("Fit/apply smoke", result_card)
        self.assertIn("HF smoke", result_card)
        self.assertIn("Live model rail", result_card)
        self.assertIn("Live sequence", result_card)

    def test_cli_build_report_creates_replayable_report_artifact(self):
        from broadcast_alpha.experiments import run_dsh, run_rqgm, run_synthetic
        from broadcast_alpha.jlens import run_jlens_gate
        from broadcast_alpha.jlens_hf_smoke import run_jlens_hf_smoke
        from broadcast_alpha.jlens_runtime import prepare_jlens_probe
        from broadcast_alpha.jlens_smoke import run_jlens_smoke
        from broadcast_alpha.ledger_stress import run_ledger_stress
        from broadcast_alpha.live_dsh import run_live_dsh, run_live_smoke
        from broadcast_alpha.live_gate import run_live_gate
        from broadcast_alpha.live_sequence import run_live_sequence

        with tempfile.TemporaryDirectory() as tmp:
            artifact_root = Path(tmp)
            run_ledger_stress(seed=42, receipt_count=10_000, artifact_root=artifact_root)
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
            prepare_jlens_probe(seed=42, artifact_root=artifact_root)
            smoke_repo = artifact_root / "fake-jlens-repo"
            smoke_python = artifact_root / "fake-python"
            smoke_repo.mkdir()
            smoke_python.write_text("# fake python\n")
            run_jlens_smoke(
                seed=42,
                artifact_root=artifact_root,
                runtime_python=smoke_python,
                source_repo=smoke_repo,
                runner=_fake_jlens_smoke_runner,
            )
            run_jlens_hf_smoke(
                seed=42,
                artifact_root=artifact_root,
                runtime_python=smoke_python,
                source_repo=smoke_repo,
                model_id="hf-internal-testing/tiny-random-gpt2",
                runner=_fake_jlens_hf_smoke_runner,
            )
            run_live_gate(seed=42, artifact_root=artifact_root, env={})
            run_live_smoke(
                seed=42,
                artifact_root=artifact_root,
                env={},
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            run_live_dsh(seed=42, artifact_root=artifact_root, env={})
            run_live_sequence(
                seed=42,
                artifact_root=artifact_root,
                env={},
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
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
            self.assertEqual(metrics["jlens_runtime_readiness_status"], "blocked_missing_dependencies")
            self.assertEqual(metrics["jlens_smoke_status"], "passed")
            self.assertEqual(metrics["jlens_hf_smoke_status"], "passed")
            self.assertTrue(metrics["jlens_hf_smoke_real_fit_apply"])
            self.assertTrue(metrics["jlens_hf_selected_labels_all_single_token"])
            self.assertFalse(metrics["jlens_hf_critical_labels_all_single_token"])
            self.assertEqual(metrics["live_model_rail_status"], "unavailable")
            self.assertEqual(metrics["live_smoke_run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_dsh_run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_dsh_prereg_id"], "PREREG_LIVE-01")
            self.assertEqual(metrics["live_dsh_hidden_verifier_pass_rate"], 0.0)
            self.assertEqual(metrics["live_sequence_status"], "blocked_before_smoke")
            self.assertEqual(metrics["live_sequence_adapter_call_count_total"], 0)
            self.assertEqual(metrics["ledger_stress_synthetic_receipt_count"], 10_000)
            self.assertTrue(metrics["ledger_stress_tamper_detection_passed"])
            self.assertEqual(metrics["verified_solve_rate"]["scarce_protected"], 0.761111)
            self.assertEqual(metrics["panel_correlation_rho"]["partitioned_disjoint_shards"], 0.28)
            self.assertEqual(metrics["candidate_ablation_rate"], 0.297222)
            self.assertIsNone(metrics["token_cost_per_solve"])

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
            self.assertEqual(metrics["jlens_runtime_readiness_status"], "blocked_missing_dependencies")
            self.assertFalse(metrics["jlens_runtime_real_probe_runnable"])
            self.assertIn(metrics["jlens_smoke_status"], {"passed", "blocked_missing_runtime"})
            self.assertIn(metrics["jlens_hf_smoke_status"], {"passed", "blocked_missing_runtime", "failed"})
            self.assertEqual(metrics["live_model_rail_status"], "unavailable")
            self.assertFalse(metrics["live_adapter_call_performed"])
            self.assertFalse(metrics["live_model_run_performed"])
            self.assertEqual(metrics["live_smoke_run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_smoke_adapter_call_count"], 0)
            self.assertEqual(metrics["live_smoke_hidden_verifier_pass_rate"], 0.0)
            self.assertEqual(metrics["live_dsh_run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_dsh_adapter_call_count"], 0)
            self.assertEqual(metrics["live_dsh_prereg_id"], "PREREG_LIVE-01")
            self.assertEqual(metrics["live_dsh_hidden_verifier_pass_count"], 0)
            self.assertEqual(metrics["live_dsh_hidden_verifier_pass_rate"], 0.0)
            self.assertEqual(metrics["live_sequence_status"], "blocked_before_smoke")
            self.assertEqual(metrics["live_sequence_adapter_call_count_total"], 0)
            self.assertEqual(metrics["live_sequence_smoke_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_sequence_pilot_status"], "not_requested")
            self.assertFalse(metrics["live_sequence_pilot_promoted"])
            self.assertTrue(metrics["live_sequence_all_child_ledgers_verified"])
            self.assertEqual(metrics["ledger_stress_synthetic_receipt_count"], 10_000)
            self.assertGreaterEqual(metrics["ledger_stress_mixed_kind_count"], 6)
            self.assertTrue(metrics["ledger_stress_tamper_detection_passed"])
            self.assertTrue(metrics["ledger_stress_ledger_verified"])
            self.assertEqual(metrics["verified_solve_rate"]["scarce_protected"], 0.761111)
            self.assertEqual(metrics["panel_correlation_rho"]["correlated_shared_context"], 0.82)
            self.assertEqual(metrics["candidate_ablation_rate"], 0.297222)
            self.assertIsNone(metrics["token_cost_per_solve"])
            self.assertTrue(metrics["all_child_ledgers_verified"])
            self.assertEqual(final_metrics["report_status"], "complete_with_deferred_jlens")
            self.assertEqual(final_metrics["live_sequence_status"], "blocked_before_smoke")
            self.assertEqual(final_metrics["ledger_stress_synthetic_receipt_count"], 10_000)
            self.assertEqual(final_metrics["verified_solve_rate"]["scarce_protected"], 0.761111)
            self.assertEqual(
                set(manifest["child_artifacts"]),
                {
                    "ledger_stress",
                    "synthetic",
                    "dsh",
                    "rqgm",
                    "jlens_gate",
                    "jlens_runtime_readiness",
                    "jlens_smoke",
                    "jlens_hf_smoke",
                    "live_model_gate",
                    "live_smoke",
                    "live_dsh_pilot",
                    "live_sequence",
                    "final_report",
                },
            )
            self.assertTrue((result.artifact_path / "source_artifacts" / "dsh_seed_42" / "seed_audit.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "live_gate_seed_42" / "provider_status.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "live_smoke_seed_42" / "task_runs.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "live_dsh_seed_42" / "task_runs.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "live_sequence_seed_42" / "manifest.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "jlens_runtime_readiness_seed_42" / "model_manifest.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "jlens_smoke_seed_42" / "metrics.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "jlens_hf_smoke_seed_42" / "metrics.json").exists())
            self.assertTrue((result.artifact_path / "source_artifacts" / "ledger_stress_seed_42" / "receipt_kind_counts.json").exists())
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
            self.assertEqual(metrics["live_smoke_run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_dsh_run_status"], "blocked_no_live_execution")
            self.assertEqual(metrics["live_sequence_status"], "blocked_before_smoke")
            self.assertIn(metrics["jlens_hf_smoke_status"], {"passed", "blocked_missing_runtime", "failed"})
            self.assertEqual(metrics["live_sequence_adapter_call_count_total"], 0)
            self.assertEqual(metrics["ledger_stress_synthetic_receipt_count"], 10_000)
            self.assertTrue(metrics["ledger_stress_tamper_detection_passed"])
            self.assertEqual(metrics["verified_solve_rate"]["scarce_protected"], 0.761111)
            self.assertEqual(metrics["candidate_ablation_rate"], 0.297222)
            self.assertIsNone(metrics["token_cost_per_solve"])
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

    def test_goal_audit_records_proved_deferred_and_incomplete_requirements(self):
        from broadcast_alpha.goal_audit import audit_goal
        from broadcast_alpha.orchestrator import run_all

        with tempfile.TemporaryDirectory() as tmp:
            artifact_root = Path(tmp)
            run_all(
                seed=42,
                tasks_per_cell=30,
                epochs=5,
                prereg_dir=APP_ROOT / "prereg",
                artifact_root=artifact_root,
                live_env={},
            )
            result = audit_goal(
                artifact_root=artifact_root,
                output_dir=artifact_root / "goal_audit_seed_42",
                repo_root=APP_ROOT,
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            requirements = json.loads((result.artifact_path / "requirements.json").read_text())
            result_card = (result.artifact_path / "result_card.md").read_text()
            ledger = (result.artifact_path / "ledger.jsonl").read_text()

        by_id = {item["id"]: item for item in requirements["items"]}
        self.assertEqual(result.run_id, "goal_audit_seed_42")
        self.assertEqual(metrics["overall_status"], "not_complete")
        self.assertGreaterEqual(metrics["proved_count"], 7)
        self.assertGreaterEqual(metrics["deferred_count"], 3)
        self.assertGreaterEqual(metrics["incomplete_count"], 1)
        self.assertEqual(by_id["macro_glassgate_lift"]["status"], "proved")
        self.assertEqual(by_id["macro_d_by_arm"]["status"], "proved")
        self.assertEqual(by_id["macro_diagnostics"]["status"], "proved")
        self.assertEqual(by_id["macro_diagnostics"]["value"]["verified_solve_rate"]["scarce_protected"], 0.761111)
        self.assertEqual(by_id["macro_diagnostics"]["value"]["panel_correlation_rho"]["correlated_shared_context"], 0.82)
        self.assertEqual(by_id["macro_diagnostics"]["value"]["candidate_ablation_rate"], 0.297222)
        self.assertIsNone(by_id["macro_diagnostics"]["value"]["token_cost_per_solve"])
        self.assertEqual(by_id["ledger_stress_10k"]["status"], "proved")
        self.assertEqual(by_id["ledger_stress_10k"]["value"]["synthetic_receipt_count"], 10_000)
        self.assertTrue(by_id["ledger_stress_10k"]["value"]["tamper_detection_passed"])
        self.assertEqual(by_id["seed_detectability_audit"]["status"], "proved")
        self.assertEqual(by_id["rqgm_epoch_trajectory"]["status"], "proved")
        self.assertEqual(by_id["jlens_or_clean_defer"]["status"], "deferred_with_record")
        self.assertEqual(by_id["bridge_rail"]["status"], "deferred_with_record")
        self.assertEqual(by_id["mechanistic_admission"]["status"], "deferred_with_record")
        self.assertEqual(by_id["live_model_backed_execution"]["status"], "incomplete")
        self.assertIn("No live model-backed adapter call", by_id["live_model_backed_execution"]["evidence"])
        self.assertIn("Goal remains incomplete", result_card)
        self.assertIn('"kind": "goal_audit_metrics"', ledger)

    def test_goal_audit_accepts_live_model_sweep_as_model_backed_evidence(self):
        from broadcast_alpha.goal_audit import audit_goal
        from broadcast_alpha.live_model_sweep import run_live_model_sweep
        from broadcast_alpha.orchestrator import run_all

        def fake_transport(_request):
            return {
                "id": "chatcmpl_fake_real_label",
                "choices": [{"message": {"content": "{\"patch\": \"x + 2\"}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
            }

        with tempfile.TemporaryDirectory() as tmp:
            artifact_root = Path(tmp)
            env_file = artifact_root / "provider.env"
            env_file.write_text(
                "OPENROUTER_API_KEY=dummy-secret-value\n"
                "OPENROUTER_MODEL_1=test/model-a\n"
            )
            run_all(
                seed=42,
                tasks_per_cell=30,
                epochs=5,
                prereg_dir=APP_ROOT / "prereg",
                artifact_root=artifact_root,
                live_env={},
            )
            run_live_model_sweep(
                seed=42,
                artifact_root=artifact_root,
                env_file=env_file,
                env={},
                api_spend_authorized=True,
                execute_live=True,
                budget_usd=25.0,
                transport=fake_transport,
                transport_label="real",
                prereg_path=APP_ROOT / "prereg" / "PREREG_LIVE-01.md",
            )
            result = audit_goal(
                artifact_root=artifact_root,
                output_dir=artifact_root / "goal_audit_seed_42",
                repo_root=APP_ROOT,
            )
            metrics = json.loads((result.artifact_path / "metrics.json").read_text())
            requirements = json.loads((result.artifact_path / "requirements.json").read_text())

        by_id = {item["id"]: item for item in requirements["items"]}
        self.assertEqual(metrics["overall_status"], "complete_with_deferred_records")
        self.assertEqual(by_id["live_model_backed_execution"]["status"], "proved")
        self.assertIn("Live model-backed execution recorded", by_id["live_model_backed_execution"]["evidence"])
        self.assertEqual(by_id["live_model_backed_execution"]["value"]["live_model_sweep_adapter_call_count_total"], 1)

    def test_cli_audit_goal_creates_replayable_audit_artifact(self):
        from broadcast_alpha.orchestrator import run_all

        with tempfile.TemporaryDirectory() as tmp:
            artifact_root = Path(tmp)
            run_all(
                seed=42,
                tasks_per_cell=30,
                epochs=5,
                prereg_dir=APP_ROOT / "prereg",
                artifact_root=artifact_root,
                live_env={},
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "broadcast_alpha",
                    "audit-goal",
                    "--artifact-root",
                    tmp,
                    "--output",
                    str(artifact_root / "goal_audit_seed_42"),
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

            self.assertEqual(payload["run_id"], "goal_audit_seed_42")
            self.assertEqual(metrics["overall_status"], "not_complete")
            self.assertTrue((artifact_path / "requirements.json").exists())

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
            self.assertIn("goal audit: not_complete", replay.stdout)

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
