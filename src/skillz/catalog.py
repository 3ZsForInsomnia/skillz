"""Every skill skillz can see: the library, plus folders pulled in by namespace settings."""

from collections.abc import Iterator

from skillz.context import Context
from skillz.library import Skill, scan_library


def all_skills(context: Context) -> list[Skill]:
    return [*scan_library(context.library), *_pulled_skills(context)]


def pulled_namespaces(context: Context) -> dict[str, str]:
    """Pulled namespace names mapped to the folder each is read from."""
    return {name: str(s.pull_from) for name, s in context.namespaces.items() if s.pull_from}


def _pulled_skills(context: Context) -> Iterator[Skill]:
    for namespace, settings in context.namespaces.items():
        if settings.pull_from is None:
            continue
        if not settings.pull_from.is_dir():
            context.warn(f"namespace {namespace!r} pulls from {settings.pull_from}, which doesn't exist")
            continue
        yield from scan_library(settings.pull_from, namespace_prefix=namespace, external=True)
