"""XDG base directory resolution."""

import os
from pathlib import Path

APP_NAME = "skillz"
MANIFEST_FILENAME = "skillz.toml"


def _xdg_dir(env_var: str, fallback: str) -> Path:
    value = os.environ.get(env_var, "").strip()
    has_absolute_override = bool(value) and Path(value).is_absolute()
    return Path(value) if has_absolute_override else Path.home() / fallback


def config_dir() -> Path:
    return _xdg_dir("XDG_CONFIG_HOME", ".config") / APP_NAME


def data_dir() -> Path:
    return _xdg_dir("XDG_DATA_HOME", ".local/share") / APP_NAME


def manifest_path() -> Path:
    return config_dir() / MANIFEST_FILENAME


def default_library_dir() -> Path:
    return data_dir() / "skills"


def expand(path: str) -> Path:
    return Path(os.path.expandvars(path)).expanduser()
