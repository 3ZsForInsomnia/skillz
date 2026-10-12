"""skillz reset: restore tracked skills to exactly what the lock records."""

from collections.abc import Sequence

from skillz.checkout import SHORT_SHA_LENGTH, Checkout
from skillz.commands.common import index_skills, select_tracked
from skillz.commands.installing import install_from_checkout
from skillz.commands.upstream import group_by_source, open_source, skill_folder
from skillz.context import Context
from skillz.library import Skill
from skillz.lock import SkillEntry, load_lock, save_lock, with_entry


def run_reset(context: Context, names: Sequence[str]) -> str:
    lock = load_lock(context.library)
    on_disk = index_skills(context)
    lines: list[str] = []
    for source_key, group in group_by_source(lock, select_tracked(lock, names)).items():
        with open_source(context, source_key) as checkout:
            for name, entry in group:
                lock = with_entry(lock, name, _reset_one(context, checkout, name, entry, on_disk.get(name)))
                save_lock(context.library, lock)
                lines.append(f"{name}: reset to {entry.commit[:SHORT_SHA_LENGTH]}")
    return "\n".join(lines)


def _reset_one(
    context: Context, checkout: Checkout, name: str, entry: SkillEntry, skill: Skill | None
) -> SkillEntry:
    checkout.fetch_commit(entry.commit)
    return install_from_checkout(
        context,
        checkout,
        namespace=entry.namespace,
        source=entry.source,
        path=entry.path,
        dest=skill_folder(context, name, entry, skill),
        rev=entry.commit,
    )
