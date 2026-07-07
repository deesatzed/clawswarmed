from pathlib import Path

from .planner import build_role_plan


def build_council_plan(goal: str, workspace: Path) -> dict:
    role_plan = build_role_plan(goal, workspace)
    return {
        "project": "claswarmed",
        "goal": goal,
        "source_pattern": "swarm-code/docs/FUSION.md",
        "roles": role_plan["roles"],
        "panels": [
            {
                "perspective": "architect",
                "assigned_model": "Gemini",
                "tool_policy": "read-only",
                "focus": "Map source evidence into system architecture and integration points.",
                "budget": {"max_tool_calls": 6, "timeout_seconds": 60},
            },
            {
                "perspective": "skeptic",
                "assigned_model": "Grok",
                "tool_policy": "read-only",
                "focus": "Find false assumptions, missing gates, and showpiece credibility risks.",
                "budget": {"max_tool_calls": 6, "timeout_seconds": 60},
            },
            {
                "perspective": "operator",
                "assigned_model": "Codex",
                "tool_policy": "read-only",
                "focus": "Turn findings into executable tasks, tests, and receipts.",
                "budget": {"max_tool_calls": 6, "timeout_seconds": 60},
            },
        ],
        "judge": {
            "assigned_model": "Claude",
            "tool_policy": "no-tools",
            "focus": "Synthesize panel outputs into accepted actions, rejected risks, and next gates.",
        },
        "synthesis_schema": [
            "consensus",
            "contradictions",
            "partial_coverage",
            "unique_insights",
            "blind_spots",
            "accepted_actions",
        ],
        "review_gates": role_plan["review_gates"],
    }

