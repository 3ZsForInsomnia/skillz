"""Keep each namespace's link_to path a symlink to that namespace's folder in the library."""

import os
from pathlib import Path

from skillz.context import Context


def sync_links(context: Context) -> None:
    for namespace, settings in context.namespaces.items():
        if settings.link_to:
            message = sync_link(context.library / namespace, settings.link_to)
            if message:
                context.warn(message)


def sync_link(target: Path, link: Path) -> str | None:
    """Create link -> target if it's missing. Never replaces anything; returns a message when acting."""
    target.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        points_to_target = link.resolve() == target.resolve()
        return None if points_to_target else f"{link} links to {os.readlink(link)}, not {target}; left as is"
    if link.exists():
        return f"{link} already exists and isn't a link to {target}; left as is"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target)
    return f"linked {link} -> {target}"
