"""skillz status: tracked skills with local edits, available updates, or other drift."""

from collections.abc import Sequence

from skillz.checkout import Checkout
from skillz.commands.diffs import edits_diff, update_diff
from skillz.commands.common import select_tracked
from skillz.commands.upstream import SkillCheck, checked_sources
from skillz.context import Context
from skillz.lock import load_lock

ALL_CLEAR = "Everything is up to date."


def run_status(context: Context, names: Sequence[str], show_diff: bool) -> str:
    lock = load_lock(context.library)
    sections: list[str] = []
    for checkout, checks in checked_sources(context, lock, select_tracked(lock, names)):
        for check in checks:
            labels = drift_labels(check)
            if labels:
                sections.append(f"{check.name} ({check.entry.namespace}): {', '.join(labels)}")
            if labels and show_diff:
                sections.extend(_diffs(checkout, check))
    return "\n".join(sections) or ALL_CLEAR


def drift_labels(check: SkillCheck) -> list[str]:
    conditions = (
        (check.skill is None, "missing locally"),
        (check.edited, "local edits"),
        (check.update_available, "update available"),
        (check.removed_upstream, "removed upstream"),
    )
    return [label for applies, label in conditions if applies]


def _diffs(checkout: Checkout, check: SkillCheck) -> list[str]:
    diffs = []
    if check.edited:
        diffs.append(edits_diff(checkout, check))
    if check.update_available:
        diffs.append(update_diff(checkout, check))
    return [diff.rstrip("\n") for diff in diffs if diff]
