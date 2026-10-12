"""Compute each skill's status by comparing the library on disk with the lock."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from skillz.library import Skill
from skillz.lock import Lock, SkillEntry

HashFn = Callable[[Path], str]


class Status(StrEnum):
    UNCHANGED = "unchanged"
    EDITED = "edited"
    UNTRACKED = "untracked"
    MISSING = "missing"
    MISPLACED = "misplaced"
    EXTERNAL = "external"


@dataclass(frozen=True)
class SkillReport:
    name: str
    namespace: str
    status: Status
    description: str
    path: Path | None
    source: str | None


def build_reports(skills: Iterable[Skill], lock: Lock, hash_fn: HashFn) -> list[SkillReport]:
    on_disk = [_report_on_disk(skill, lock.skills.get(skill.name), hash_fn) for skill in skills]
    names_on_disk = {report.name for report in on_disk}
    missing = [
        _report_missing(name, entry) for name, entry in lock.skills.items() if name not in names_on_disk
    ]
    return sorted([*on_disk, *missing], key=lambda report: (report.namespace, report.name))


def classify(skill: Skill, entry: SkillEntry | None, hash_fn: HashFn) -> Status:
    if skill.external:
        return Status.EXTERNAL
    if entry is None:
        return Status.UNTRACKED
    if skill.namespace != entry.namespace:
        return Status.MISPLACED
    is_unedited = hash_fn(skill.path) == entry.content_hash
    return Status.UNCHANGED if is_unedited else Status.EDITED


def _report_on_disk(skill: Skill, entry: SkillEntry | None, hash_fn: HashFn) -> SkillReport:
    return SkillReport(
        name=skill.name,
        namespace=skill.namespace,
        status=classify(skill, entry, hash_fn),
        description=skill.description,
        path=skill.path,
        source=entry.source if entry else None,
    )


def _report_missing(name: str, entry: SkillEntry) -> SkillReport:
    return SkillReport(
        name=name,
        namespace=entry.namespace,
        status=Status.MISSING,
        description="",
        path=None,
        source=entry.source,
    )
