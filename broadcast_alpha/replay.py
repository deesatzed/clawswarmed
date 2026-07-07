import json
from pathlib import Path


def replay_context(artifact_path: Path, agent_id: str, step: int) -> str:
    contexts = json.loads((artifact_path / "replay" / "contexts.json").read_text())
    return contexts[agent_id][str(step)]

