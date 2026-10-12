"""User settings from skillz.toml: the library location and per-namespace options."""

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from skillz import paths

TOP_LEVEL_KEYS = frozenset({"library", "namespaces"})
NAMESPACE_KEYS = frozenset({"link_to", "pull_from"})


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class NamespaceSettings:
    link_to: Path | None = None
    pull_from: Path | None = None


@dataclass(frozen=True)
class Manifest:
    library: Path
    namespaces: Mapping[str, NamespaceSettings] = field(default_factory=dict)


def load_manifest(path: Path) -> Manifest:
    if not path.exists():
        return Manifest(library=paths.default_library_dir())
    try:
        raw = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise ManifestError(f"{path}: {error}") from error
    return parse_manifest(raw)


def parse_manifest(raw: Mapping[str, object]) -> Manifest:
    _reject_unknown_keys(raw, TOP_LEVEL_KEYS, "top level")
    library = _optional_path(raw, "library", "") or paths.default_library_dir()
    namespaces = _table(raw.get("namespaces", {}), "namespaces")
    return Manifest(
        library=library,
        namespaces={name: _parse_namespace(name, settings) for name, settings in namespaces.items()},
    )


def _parse_namespace(name: str, raw: object) -> NamespaceSettings:
    where = f"namespaces.{name}"
    _validate_namespace_name(name, where)
    settings = _table(raw, where)
    _reject_unknown_keys(settings, NAMESPACE_KEYS, where)
    link_to = _optional_path(settings, "link_to", where)
    pull_from = _optional_path(settings, "pull_from", where)
    if link_to and pull_from:
        raise ManifestError(f"{where}: link_to and pull_from cannot both be set")
    return NamespaceSettings(link_to=link_to, pull_from=pull_from)


def _validate_namespace_name(name: str, where: str) -> None:
    parts = PurePosixPath(name).parts
    is_relative_and_clean = bool(parts) and parts[0] != "/" and ".." not in parts
    if not is_relative_and_clean:
        raise ManifestError(f"{where}: namespace must be a relative folder path without '..'")


def _table(value: object, where: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"{where}: expected a table")
    return value


def _optional_path(raw: Mapping[str, object], key: str, where: str) -> Path | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        label = f"{where}.{key}" if where else key
        raise ManifestError(f"{label}: expected a non-empty path string")
    return paths.expand(value)


def _reject_unknown_keys(raw: Mapping[str, object], allowed: frozenset[str], where: str) -> None:
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ManifestError(f"{where}: unknown key(s): {', '.join(unknown)}")
