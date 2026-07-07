from pathlib import Path


def build_showpiece_plan(project: str) -> dict:
    return {
        "project": project,
        "title": "CAM_Codx showpiece build plan",
        "phases": [
            {
                "name": "Evidence Inventory",
                "goal": "Load the source docs, paper, and reference repos with provenance.",
            },
            {
                "name": "Council Planning",
                "goal": "Assign model roles and synthesize a bounded multi-agent build plan.",
            },
            {
                "name": "RQGM Epoch Demo",
                "goal": "Show frozen evaluator slots, challenger scoring, replacement, and lineage.",
            },
            {
                "name": "Dashboard Proof",
                "goal": "Expose evidence, plan, epoch decisions, and receipts in a local UI.",
            },
            {
                "name": "CAM Case Study",
                "goal": "Save verification receipts and explain how CAM_Codx/CAM_CAM guided the build.",
            },
        ],
    }


def build_role_plan(goal: str, workspace: Path) -> dict:
    return {
        "project": "claswarmed",
        "goal": goal,
        "workspace": str(workspace),
        "roles": [
            {
                "model": "Codex",
                "primary_job": "program manager",
                "why": "Owns orchestration, code changes, verification, and final decisions.",
                "source": "GOAL.md program manager model",
            },
            {
                "model": "Grok",
                "primary_job": "architecture critic",
                "why": "Challenges assumptions, identifies blind spots, and reviews reasoning.",
                "source": "bld1.md strengths mapping",
            },
            {
                "model": "Claude",
                "primary_job": "code quality reviewer",
                "why": "Reviews implementation quality, safety, maintainability, and docs.",
                "source": "bld1.md strengths mapping",
            },
            {
                "model": "Gemini",
                "primary_job": "long-context analyst",
                "why": "Synthesizes large source evidence and checks cross-document coherence.",
                "source": "bld1.md and bld3.md architecture notes",
            },
            {
                "model": "OpenAI-compatible profile",
                "primary_job": "runtime execution profile",
                "why": "Matches swarm-code's bring-your-own OpenAI-compatible endpoint model.",
                "source": "swarm-code/README.md configuration",
            },
        ],
        "review_gates": [
            {
                "name": "source-evidence boundary",
                "check": "Do not mutate source repos unless explicitly approved.",
            },
            {
                "name": "council synthesis",
                "check": "Architect, skeptic, and operator outputs must be synthesized before action.",
            },
            {
                "name": "rqgm evaluator checkpoint",
                "check": "Evaluator replacement decisions occur only at epoch boundaries.",
            },
            {
                "name": "verification receipts",
                "check": "Tests, smoke commands, and CAM checks are recorded before claims.",
            },
        ],
    }
