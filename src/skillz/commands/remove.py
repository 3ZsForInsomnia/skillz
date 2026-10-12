"""skillz remove: delete tracked skills and drop them from the lock."""

import shutil
from collections.abc import Sequence
from functools import reduce

from skillz.commands.common import CANCELLED, index_skills
from skillz.context import Context
from skillz.errors import SkillzError
from skillz.hashing import content_hash
from skillz.library import Skill
from skillz.lock import Lock, load_lock, save_lock, without_skill


def run_remove(context: Context, requested: Sequence[str]) -> str:
    names = list(dict.fromkeys(requested))
    lock = load_lock(context.library)
    untracked = [name for name in names if name not in lock.skills]
    if untracked:
        raise SkillzError(f"not tracked by skillz (delete these by hand): {', '.join(untracked)}")
    on_disk = {name: skill for name, skill in index_skills(context).items() if name in names}
    if not context.confirm(removal_question(names, _edited(on_disk, lock))):
        return CANCELLED
    for skill in on_disk.values():
        shutil.rmtree(skill.path)
    save_lock(context.library, reduce(without_skill, names, lock))
    return f"Removed: {', '.join(names)}"


def removal_question(names: Sequence[str], edited: Sequence[str]) -> str:
    warning = f" These have local edits that will be lost: {', '.join(edited)}." if edited else ""
    return f"Remove {', '.join(names)}?{warning}"


def _edited(on_disk: dict[str, Skill], lock: Lock) -> list[str]:
    return sorted(
        name for name, skill in on_disk.items() if content_hash(skill.path) != lock.skills[name].content_hash
    )
