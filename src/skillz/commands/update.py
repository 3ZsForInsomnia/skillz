"""skillz update: replace tracked skills with their upstream versions."""

from collections.abc import Sequence

from skillz.checkout import Checkout
from skillz.commands.installing import install_from_checkout
from skillz.commands.status import ALL_CLEAR
from skillz.commands.common import select_tracked
from skillz.commands.upstream import SkillCheck, checked_sources, skill_folder
from skillz.context import Context
from skillz.errors import SkillzError
from skillz.lock import Lock, load_lock, save_lock, with_entry


def run_update(context: Context, names: Sequence[str], check_only: bool, force: bool) -> str:
    if force and not names:
        raise SkillzError("-f/--force needs skill names, so it can't overwrite every edited skill at once")
    lock = load_lock(context.library)
    lines: list[str] = []
    for checkout, checks in checked_sources(context, lock, select_tracked(lock, names)):
        for check in checks:
            if check.removed_upstream:
                lines.append(f"{check.name}: removed upstream; left as is")
            elif check.update_available:
                outcome, lock = _update_one(context, checkout, check, lock, check_only, force)
                lines.append(f"{check.name}: {outcome}")
    return "\n".join(lines) or ALL_CLEAR


def _update_one(
    context: Context, checkout: Checkout, check: SkillCheck, lock: Lock, check_only: bool, force: bool
) -> tuple[str, Lock]:
    if check_only:
        return "update available", lock
    if check.edited and not force:
        return "skipped, has local edits (rerun with its name and -f to overwrite)", lock
    entry = install_from_checkout(
        context,
        checkout,
        namespace=check.entry.namespace,
        source=check.entry.source,
        path=check.entry.path,
        dest=skill_folder(context, check.name, check.entry, check.skill),
    )
    updated = with_entry(lock, check.name, entry)
    save_lock(context.library, updated)
    return "updated", updated
