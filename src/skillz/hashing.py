"""Content hash of a skill folder, used to detect local edits."""

import hashlib
import os
from collections.abc import Iterator
from pathlib import Path

HASH_PREFIX = "sha256:"
IGNORED_NAMES = frozenset({".DS_Store"})


def content_hash(folder: Path) -> str:
    digest = hashlib.sha256()
    for relative in sorted(_files_under(folder)):
        data = (folder / relative).read_bytes()
        digest.update(f"{relative}\0{len(data)}\0".encode())
        digest.update(data)
    return HASH_PREFIX + digest.hexdigest()


def _files_under(folder: Path) -> Iterator[str]:
    for current, _dirnames, filenames in os.walk(folder, followlinks=True):
        for name in filenames:
            if name not in IGNORED_NAMES:
                yield (Path(current) / name).relative_to(folder).as_posix()
