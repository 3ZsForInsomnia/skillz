import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from skillz.cli import main
from skillz.context import Context


def run_cli(*argv: str, context: Context | None = None) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(argv), context)
    return code, stdout.getvalue(), stderr.getvalue()


def read_lock(library: Path) -> dict:
    return json.loads((library / "skillz.lock.json").read_text())


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


def git(repo: Path, *args: str) -> str:
    isolated = ["-c", "core.fsmonitor=false", "-c", "maintenance.auto=false", "-c", "core.hooksPath=/dev/null"]
    return subprocess.run(["git", *isolated, *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def make_source_repo(path: Path, files: dict[str, str]) -> Path:
    """Create a committed git repo containing files, given as {relative path: content}."""
    path.mkdir(parents=True)
    git(path, "init", "--quiet", "--initial-branch=main")
    for relative, content in files.items():
        (path / relative).parent.mkdir(parents=True, exist_ok=True)
        (path / relative).write_text(content)
    commit_all(path)
    return path


def commit_all(repo: Path, message: str = "update") -> None:
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "--quiet", "-m", message)


def skill_file(name: str) -> str:
    return f"---\nname: {name}\ndescription: The {name} skill.\n---\n"


class FakeTerminal:
    """Answers prompts from a fixed list and records every question and warning."""

    def __init__(self, *answers: bool) -> None:
        self.answers = list(answers)
        self.questions: list[str] = []
        self.warnings: list[str] = []

    def confirm(self, question: str) -> bool:
        self.questions.append(question)
        if not self.answers:
            raise AssertionError(f"unexpected prompt: {question}")
        return self.answers.pop(0)

    def context(self, library: Path, repo: Path | None = None) -> Context:
        return Context(
            library=library,
            confirm=self.confirm,
            clone_url=lambda spec: f"file://{repo}",
            warn=self.warnings.append,
        )


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
