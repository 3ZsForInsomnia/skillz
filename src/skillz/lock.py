"""The tool-owned lock file: installed sources and skills, with the hashes to check them."""

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

from skillz.errors import SkillzError

LOCK_FILENAME = "skillz.lock.json"
LOCK_VERSION = 1


class LockError(SkillzError):
    pass


@dataclass(frozen=True)
class SourceEntry:
    ref: str | None
    skills: tuple[str, ...]


@dataclass(frozen=True)
class SkillEntry:
    namespace: str
    source: str
    path: str
    commit: str
    upstream_hash: str
    content_hash: str
    installed_at: str


@dataclass(frozen=True)
class Lock:
    sources: Mapping[str, SourceEntry] = field(default_factory=dict)
    skills: Mapping[str, SkillEntry] = field(default_factory=dict)


def lock_path(library: Path) -> Path:
    return library / LOCK_FILENAME


def load_lock(library: Path) -> Lock:
    path = lock_path(library)
    if not path.exists():
        return Lock()
    try:
        return lock_from_dict(json.loads(path.read_text()))
    except (json.JSONDecodeError, LockError) as error:
        raise LockError(f"{path}: {error}") from error


def save_lock(library: Path, lock: Lock) -> None:
    text = json.dumps(lock_to_dict(lock), indent=2, sort_keys=True) + "\n"
    _write_atomically(lock_path(library), text)


def with_installed(lock: Lock, source_key: str, ref: str | None, entries: Mapping[str, SkillEntry]) -> Lock:
    existing = lock.sources.get(source_key)
    names = tuple(sorted({*(existing.skills if existing else ()), *entries}))
    return Lock(
        sources={**lock.sources, source_key: SourceEntry(ref=ref, skills=names)},
        skills={**lock.skills, **entries},
    )


def without_skill(lock: Lock, name: str) -> Lock:
    source_key = lock.skills[name].source
    skills = {key: entry for key, entry in lock.skills.items() if key != name}
    sources = {key: source for key, source in lock.sources.items() if key != source_key}
    source = lock.sources.get(source_key)
    remaining_names = tuple(n for n in source.skills if n != name) if source else ()
    if remaining_names:
        sources[source_key] = replace(source, skills=remaining_names)
    return Lock(sources=sources, skills=skills)


def with_entry(lock: Lock, name: str, entry: SkillEntry) -> Lock:
    return Lock(sources=lock.sources, skills={**lock.skills, name: entry})


def with_namespace(lock: Lock, name: str, namespace: str) -> Lock:
    return with_entry(lock, name, replace(lock.skills[name], namespace=namespace))


def lock_to_dict(lock: Lock) -> dict[str, object]:
    return {
        "version": LOCK_VERSION,
        "sources": {name: {"ref": s.ref, "skills": list(s.skills)} for name, s in lock.sources.items()},
        "skills": {name: asdict(entry) for name, entry in lock.skills.items()},
    }


def lock_from_dict(raw: Mapping[str, object]) -> Lock:
    if raw.get("version") != LOCK_VERSION:
        raise LockError(f"unsupported lock version {raw.get('version')!r}")
    return Lock(
        sources={name: _source_from_dict(name, s) for name, s in _mapping(raw, "sources").items()},
        skills={name: _skill_from_dict(name, s) for name, s in _mapping(raw, "skills").items()},
    )


def _source_from_dict(name: str, raw: object) -> SourceEntry:
    try:
        return SourceEntry(ref=raw["ref"], skills=tuple(raw["skills"]))
    except (KeyError, TypeError) as error:
        raise LockError(f"sources.{name}: malformed entry") from error


def _skill_from_dict(name: str, raw: object) -> SkillEntry:
    try:
        return SkillEntry(**raw)
    except TypeError as error:
        raise LockError(f"skills.{name}: malformed entry ({error})") from error


def _mapping(raw: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = raw.get(key, {})
    if not isinstance(value, Mapping):
        raise LockError(f"{key}: expected an object")
    return value


def _write_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, suffix=".tmp") as handle:
        handle.write(text)
    os.replace(handle.name, path)
