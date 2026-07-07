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

