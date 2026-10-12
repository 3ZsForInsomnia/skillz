"""Temporary shallow, blob-less clones of a source repo, deleted when the command finishes.

Skill folders are exported from the clone on demand, so only their files are downloaded.
"""

import subprocess
import tempfile
from collections.abc import Container, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from skillz.errors import SkillzError
from skillz.library import SKILL_FILE

HEAD = "HEAD"
REPO_ROOT = ""
SHORT_SHA_LENGTH = 12
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
class Exported:
    folder: Path
    root: Path


@dataclass(frozen=True)
class Checkout:
    root: Path
    commit: str
    skill_paths: Mapping[str, tuple[str, ...]]

    def tree_hash(self, path: str, rev: str = HEAD) -> str:
        return run_git(["rev-parse", f"{rev}:{path}"], cwd=self.root).strip()

    def has_path(self, path: str, rev: str = HEAD) -> bool:
        return _git(["cat-file", "-e", f"{rev}:{path}"], cwd=self.root).returncode == 0

    def fetch_commit(self, commit: str) -> None:
        if commit == self.commit:
            return
        try:
            run_git(["fetch", "--quiet", "--depth", "1", "--filter=blob:none", "origin", commit], cwd=self.root)
        except GitError as error:
            raise GitError(f"commit {commit[:SHORT_SHA_LENGTH]} is no longer available upstream") from error

    def export(self, path: str, rev: str = HEAD) -> Exported:
        export_root = self.root.parent / "exports" / rev
        export_root.mkdir(parents=True, exist_ok=True)
        run_git([f"--work-tree={export_root}", "checkout", "--quiet", rev, "--", path or "."], cwd=self.root)
        return Exported(folder=export_root / path, root=export_root)


@contextmanager
def open_checkout(url: str, ref: str | None, repo_name: str) -> Iterator[Checkout]:
    with tempfile.TemporaryDirectory(prefix="skillz-") as temp:
        root = Path(temp) / "repo"
        branch = ["--branch", ref] if ref else []
        run_git(["clone", "--quiet", "--depth", "1", "--filter=blob:none", "--no-checkout", *branch, url, str(root)])
        files = run_git(["ls-tree", "-r", "-z", "--name-only", HEAD], cwd=root).split("\0")
        commit = run_git(["rev-parse", HEAD], cwd=root).strip()
        yield Checkout(root=root, commit=commit, skill_paths=find_skill_paths(files, repo_name))


def find_skill_paths(files: Sequence[str], repo_name: str) -> dict[str, tuple[str, ...]]:
    folders = [_parent(file) for file in files if PurePosixPath(file).name == SKILL_FILE]
    outermost = [folder for folder in folders if not any(_is_inside(folder, other) for other in folders)]
    grouped: dict[str, tuple[str, ...]] = {}
    for folder in sorted(outermost):
        name = PurePosixPath(folder).name or repo_name
        grouped[name] = (*grouped.get(name, ()), folder)
    return grouped


def run_git(args: Sequence[str], cwd: Path | None = None, ok_codes: Container[int] = (0,)) -> str:
    result = _git(args, cwd)
    if result.returncode not in ok_codes:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _git(args: Sequence[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *ISOLATED_GIT, *args], cwd=cwd, capture_output=True, text=True)


def _parent(file: str) -> str:
    parent = PurePosixPath(file).parent.as_posix()
    return REPO_ROOT if parent == "." else parent


def _is_inside(folder: str, other: str) -> bool:
    if folder == other:
        return False
    return other == REPO_ROOT or folder.startswith(f"{other}/")
