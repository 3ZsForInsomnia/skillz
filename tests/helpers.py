import json
import tempfile
import unittest
from pathlib import Path


class TempDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)


def write_skill(library: Path, namespace: str, name: str, description: str = "A test skill.") -> Path:
    folder = library / namespace / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n")
    return folder


def write_lock(library: Path, skills: dict[str, dict], sources: dict[str, dict] | None = None) -> None:
    library.mkdir(parents=True, exist_ok=True)
    lock = {"version": 1, "sources": sources or {}, "skills": skills}
    (library / "skillz.lock.json").write_text(json.dumps(lock))


def lock_entry(namespace: str, content_hash: str = "sha256:abc", source: str = "acme/skills") -> dict:
    return {
        "namespace": namespace,
        "source": source,
        "path": "skills/x",
        "commit": "deadbeef",
        "upstream_hash": "cafef00d",
        "content_hash": content_hash,
        "installed_at": "2026-10-12T00:00:00Z",
    }
