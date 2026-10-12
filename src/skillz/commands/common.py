"""Helpers shared by commands that change the library."""

from skillz.context import Context
from skillz.errors import SkillzError
from skillz.library import Skill, is_valid_namespace, scan_library

CANCELLED = "Cancelled."


def index_skills(context: Context) -> dict[str, Skill]:
    """Skills on disk by name. Names must be unique across the library."""
    index: dict[str, Skill] = {}
    for skill in scan_library(context.library):
        if skill.name in index:
            namespaces = f"{index[skill.name].namespace or '-'} and {skill.namespace or '-'}"
            raise SkillzError(f"skill {skill.name!r} exists in more than one namespace ({namespaces})")
        index[skill.name] = skill
    return index


def find_skill(context: Context, name: str) -> Skill:
    skill = index_skills(context).get(name)
    if skill is None:
        raise SkillzError(f"no skill named {name!r} in the library")
    return skill


def require_valid_namespace(namespace: str) -> None:
    if not is_valid_namespace(namespace):
        raise SkillzError(f"invalid namespace {namespace!r}; use a relative folder path without '..'")


def ensure_namespace(context: Context, namespace: str, create_without_asking: bool = False) -> bool:
    folder = context.library / namespace
    if folder.is_dir():
        return True
    question = f'Namespace "{namespace}" doesn\'t exist. Create it?'
    if not (create_without_asking or context.confirm(question)):
        return False
    folder.mkdir(parents=True)
    return True
