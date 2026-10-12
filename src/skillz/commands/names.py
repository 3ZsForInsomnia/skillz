"""Hidden commands that print skill names and namespaces, one per line, for shell completion."""

from skillz.catalog import all_skills, pulled_namespaces
from skillz.context import Context
from skillz.library import namespace_folders
from skillz.lock import load_lock


def run_names(context: Context, tracked_only: bool, managed_only: bool) -> str:
    if tracked_only:
        return "\n".join(sorted(load_lock(context.library).skills))
    skills = all_skills(context)
    return "\n".join(sorted(skill.name for skill in skills if not (managed_only and skill.external)))


def run_namespaces(context: Context) -> str:
    """Namespaces skillz can write to: library folders plus configured ones, minus pulled ones."""
    pulled = pulled_namespaces(context)
    candidates = {*namespace_folders(context.library), *context.namespaces}
    return "\n".join(sorted(name for name in candidates if name not in pulled))
