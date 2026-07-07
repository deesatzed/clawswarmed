from pathlib import Path


EVIDENCE = [
    ("bld1.md", "product vision", "document"),
    ("bld2.md", "runtime foundation review", "document"),
    ("bld3.md", "RQGM/EvoClaw architecture plan", "document"),
    ("2606.26294v2.pdf", "RQGM primary research paper", "paper"),
    ("swarm-code/", "persistent multi-agent runtime reference", "repo"),
    ("openscience/", "adjacent reference repo", "repo"),
]


def _summarize(path: Path) -> dict:
    if not path.exists():
        return {"present": False, "size_bytes": 0}
    if path.is_dir():
        file_count = sum(1 for item in path.rglob("*") if item.is_file() and ".git" not in item.parts)
        return {"present": True, "size_bytes": 0, "file_count": file_count}
    return {"present": True, "size_bytes": path.stat().st_size}


def build_inventory(workspace: Path) -> dict:
    items = []
    for relative, role, kind in EVIDENCE:
        path = workspace / relative
        item = {
            "path": relative,
            "role": role,
            "kind": kind,
        }
        item.update(_summarize(path))
        items.append(item)

    return {
        "project": "claswarmed",
        "workspace": str(workspace),
        "items": items,
    }

