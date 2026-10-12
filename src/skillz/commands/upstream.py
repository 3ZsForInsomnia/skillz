"""Compare tracked skills with their sources: local edits, available updates, removals."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from skillz.checkout import Checkout, open_checkout
from skillz.commands.common import index_skills
from skillz.context import Context
from skillz.hashing import content_hash
from skillz.library import Skill
from skillz.lock import Lock, SkillEntry
from skillz.sources import source_from_key


@dataclass(frozen=True)
class SkillCheck:
    name: str
    entry: SkillEntry
    skill: Skill | None
    edited: bool
    update_available: bool
    removed_upstream: bool


def group_by_source(lock: Lock, names: Sequence[str]) -> dict[str, list[tuple[str, SkillEntry]]]:
    groups: dict[str, list[tuple[str, SkillEntry]]] = {}
    for name in names:
        entry = lock.skills[name]
        groups.setdefault(entry.source, []).append((name, entry))
    return groups


@contextmanager
def open_source(context: Context, source_key: str) -> Iterator[Checkout]:
    spec = source_from_key(source_key)
    with open_checkout(context.clone_url(spec), spec.ref, spec.repo) as checkout:
        yield checkout


def checked_sources(context: Context, lock: Lock, names: Sequence[str]) -> Iterator[tuple[Checkout, list[SkillCheck]]]:
    """Yield each source's open checkout with the checks for its skills, one clone per source."""
    on_disk = index_skills(context)
    for source_key, group in group_by_source(lock, names).items():
        with open_source(context, source_key) as checkout:
            yield checkout, [check_skill(checkout, name, entry, on_disk.get(name)) for name, entry in group]


def check_skill(checkout: Checkout, name: str, entry: SkillEntry, skill: Skill | None) -> SkillCheck:
    removed_upstream = not checkout.has_path(entry.path)
    return SkillCheck(
        name=name,
        entry=entry,
        skill=skill,
        edited=skill is not None and content_hash(skill.path) != entry.content_hash,
        update_available=not removed_upstream and checkout.tree_hash(entry.path) != entry.upstream_hash,
        removed_upstream=removed_upstream,
    )


def skill_folder(context: Context, name: str, entry: SkillEntry, skill: Skill | None) -> Path:
    """Where a tracked skill lives on disk, or where it belongs if it's missing."""
    return skill.path if skill else context.library / entry.namespace / name
