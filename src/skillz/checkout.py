"""Temporary sparse clones of a source repo, deleted when the command finishes."""

import subprocess
import tempfile
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from skillz.errors import SkillzError
from skillz.library import SKILL_FILE

REPO_ROOT = ""
# Clones are throwaway: keep user hooks, background maintenance, and the fsmonitor daemon
# out of them, since the latter two write into .git while the clone is being deleted.
ISOLATED_GIT = (
    "-c", "core.fsmonitor=false",
    "-c", "maintenance.auto=false",
    "-c", "core.hooksPath=/dev/null",
)


class GitError(SkillzError):
    pass


@dataclass(frozen=True)
class Checkout:
    root: Path
    commit: str
    skill_paths: Mapping[str, tuple[str, ...]]

    def tree_hash(self, path: str) -> str:
        return run_git(["rev-parse", f"HEAD:{path}"], cwd=self.root).strip()

    def folder(self, path: str) -> Path:
        return self.root / path

    def materialize(self, paths: Iterable[str]) -> None:
        patterns = [_sparse_pattern(path) for path in paths]
        run_git(["sparse-checkout", "set", "--no-cone", *patterns], cwd=self.root)
        run_git(["checkout", "--quiet"], cwd=self.root)


@contextmanager
def open_checkout(url: str, ref: str | None, repo_name: str) -> Iterator[Checkout]:
    with tempfile.TemporaryDirectory(prefix="skillz-") as temp:
        root = Path(temp) / "repo"
        branch = ["--branch", ref] if ref else []
        run_git(["clone", "--quiet", "--depth", "1", "--filter=blob:none", "--no-checkout", *branch, url, str(root)])
        files = run_git(["ls-tree", "-r", "-z", "--name-only", "HEAD"], cwd=root).split("\0")
        commit = run_git(["rev-parse", "HEAD"], cwd=root).strip()
        yield Checkout(root=root, commit=commit, skill_paths=find_skill_paths(files, repo_name))


def find_skill_paths(files: Sequence[str], repo_name: str) -> dict[str, tuple[str, ...]]:
    folders = [_parent(file) for file in files if PurePosixPath(file).name == SKILL_FILE]
    outermost = [folder for folder in folders if not any(_is_inside(folder, other) for other in folders)]
    grouped: dict[str, tuple[str, ...]] = {}
    for folder in sorted(outermost):
        name = PurePosixPath(folder).name or repo_name
        grouped[name] = (*grouped.get(name, ()), folder)
    return grouped


def run_git(args: Sequence[str], cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *ISOLATED_GIT, *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _parent(file: str) -> str:
    parent = PurePosixPath(file).parent.as_posix()
    return REPO_ROOT if parent == "." else parent


def _is_inside(folder: str, other: str) -> bool:
    if folder == other:
        return False
    return other == REPO_ROOT or folder.startswith(f"{other}/")


def _sparse_pattern(path: str) -> str:
    return "/*" if path == REPO_ROOT else f"/{path}/"
