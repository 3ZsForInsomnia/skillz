"""Plain git diffs for status -d: local edits, and what an update would change."""

import shutil
import tempfile
from pathlib import Path

from skillz.checkout import Checkout, run_git
from skillz.commands.upstream import SkillCheck
from skillz.hashing import IGNORED_NAMES

DIFF_FOUND = 1


def edits_diff(checkout: Checkout, check: SkillCheck) -> str:
    """The locked version against the local folder."""
    checkout.fetch_commit(check.entry.commit)
    locked = checkout.export(check.entry.path, check.entry.commit).folder
    return folder_diff(check.name, ("locked", locked), ("local", check.skill.path if check.skill else None))


def update_diff(checkout: Checkout, check: SkillCheck) -> str:
    """The local folder against upstream: exactly what an update would change on disk."""
    upstream = checkout.export(check.entry.path).folder
    return folder_diff(check.name, ("local", check.skill.path if check.skill else None), ("upstream", upstream))


def folder_diff(name: str, old: tuple[str, Path | None], new: tuple[str, Path | None]) -> str:
    with tempfile.TemporaryDirectory(prefix="skillz-diff-") as temp:
        for label, folder in (old, new):
            _stage(folder, Path(temp) / label / name)
        sides = [f"{label}/{name}" for label, _ in (old, new)]
        return run_git(["diff", "--no-index", "--no-prefix", *sides], cwd=Path(temp), ok_codes=(0, DIFF_FOUND))


def _stage(folder: Path | None, dest: Path) -> None:
    if folder is None:
        dest.mkdir(parents=True)
        return
    shutil.copytree(folder, dest, symlinks=True, ignore=shutil.ignore_patterns(*IGNORED_NAMES))
