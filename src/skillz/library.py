"""Scan the library for skill folders: any folder containing SKILL.md."""

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from skillz.frontmatter import read_frontmatter

SKILL_FILE = "SKILL.md"


def is_valid_namespace(name: str) -> bool:
    parts = PurePosixPath(name).parts
    return bool(parts) and parts[0] != "/" and ".." not in parts


@dataclass(frozen=True)
class Skill:
    name: str
    namespace: str
    path: Path
    description: str
    external: bool = False


def scan_library(root: Path, namespace_prefix: str = "", external: bool = False) -> list[Skill]:
    """Find skills under root. External scans (pulled folders) put every namespace under a prefix."""
    if not root.is_dir():
        return []
    return sorted(
        (_read_skill(root, folder, namespace_prefix, external) for folder in _skill_folders(root)),
        key=lambda skill: (skill.namespace, skill.name),
    )


def namespace_folders(root: Path) -> list[str]:
    """Every folder in the library that isn't a skill or inside one."""
    namespaces = []
    for current, dirnames, filenames in os.walk(root):
        folder = Path(current)
        is_skill = SKILL_FILE in filenames and folder != root
        dirnames[:] = [] if is_skill else [name for name in dirnames if not name.startswith(".")]
        if folder != root and not is_skill:
            namespaces.append(folder.relative_to(root).as_posix())
    return sorted(namespaces)


def _skill_folders(root: Path) -> Iterator[Path]:
    visited: set[Path] = set()
    for current, dirnames, filenames in os.walk(root, followlinks=True):
        folder = Path(current)
        real = folder.resolve()
        already_seen = real in visited
        visited.add(real)
        is_skill = SKILL_FILE in filenames and folder != root
        should_descend = not (already_seen or is_skill)
        dirnames[:] = [name for name in dirnames if should_descend and not name.startswith(".")]
        if is_skill and not already_seen:
            yield folder


def _read_skill(root: Path, folder: Path, namespace_prefix: str, external: bool) -> Skill:
    frontmatter = read_frontmatter((folder / SKILL_FILE).read_text(errors="replace"))
    return Skill(
        name=folder.name,
        namespace=_namespace_of(root, folder, namespace_prefix),
        path=folder,
        description=frontmatter.get("description", ""),
        external=external,
    )


def _namespace_of(root: Path, folder: Path, prefix: str) -> str:
    relative = folder.parent.relative_to(root).as_posix()
    parts = [part for part in (prefix, "" if relative == "." else relative) if part]
    return "/".join(parts)
