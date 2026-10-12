"""Everything a command needs from the outside world, passed in so tests can replace it."""

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from skillz.sources import SourceSpec

YES_ANSWERS = frozenset({"y", "yes"})


@dataclass(frozen=True)
class Context:
    library: Path
    confirm: Callable[[str], bool]
    clone_url: Callable[[SourceSpec], str]
    warn: Callable[[str], None]


def confirm_on_terminal(question: str) -> bool:
    if not sys.stdin.isatty():
        warn_on_stderr(f"{question} [y/N] no terminal to ask on; answering no")
        return False
    return input(f"{question} [y/N] ").strip().lower() in YES_ANSWERS


def warn_on_stderr(message: str) -> None:
    print(f"skillz: {message}", file=sys.stderr)
