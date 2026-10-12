"""skillz move: move a skill to another namespace, keeping the lock in step."""

import shutil

from skillz.commands.common import CANCELLED, ensure_namespace, find_skill, require_valid_namespace
from skillz.context import Context
from skillz.errors import SkillzError
from skillz.lock import load_lock, save_lock, with_namespace


def run_move(context: Context, name: str, namespace: str) -> str:
    require_valid_namespace(namespace)
    lock = load_lock(context.library)
    skill = find_skill(context, name)
    if skill.namespace == namespace:
        raise SkillzError(f"{name} is already in {namespace}")
    dest = context.library / namespace / name
    if dest.exists():
        raise SkillzError(f"{dest} already exists")
    if not ensure_namespace(context, namespace):
        return CANCELLED
    shutil.move(skill.path, dest)
    if name in lock.skills:
        save_lock(context.library, with_namespace(lock, name, namespace))
    return f"Moved {name}: {skill.namespace or '-'} -> {namespace}"
