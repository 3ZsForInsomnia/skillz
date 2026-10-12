"""The tool-owned lock file: installed sources and skills, with the hashes to check them."""

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

LOCK_FILENAME = "skillz.lock.json"
LOCK_VERSION = 1


class LockError(ValueError):
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
