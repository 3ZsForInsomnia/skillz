"""skillz add: download skills from a source into a namespace and record them in the lock."""

import shutil
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path, PurePosixPath

from skillz.checkout import Checkout, open_checkout
from skillz.commands.common import CANCELLED, ensure_namespace, index_skills, require_writable_namespace
from skillz.commands.installing import install_from_checkout
from skillz.context import Context
from skillz.errors import SkillzError
from skillz.lock import SkillEntry, load_lock, save_lock, with_installed
from skillz.sources import SourceSpec, parse_source


def run_add(context: Context, source: str, names: Sequence[str], namespace: str | None) -> str:
    spec = parse_source(source)
    if spec.path and names:
        raise SkillzError("a skill folder URL installs exactly that skill; don't also pass skill names")
    target = namespace or spec.default_namespace
    require_writable_namespace(context, target)
    lock = load_lock(context.library)
    with open_checkout(context.clone_url(spec), spec.ref, spec.repo) as checkout:
        chosen = choose_skills(checkout.skill_paths, spec, names, checkout.tree_hash)
        _reject_existing(context, chosen, lock.skills)
        if not ensure_namespace(context, target, create_without_asking=namespace is None):
            return CANCELLED
        entries = _install_all(context, checkout, spec, chosen, target)
        save_lock(context.library, with_installed(lock, spec.key, spec.ref, entries))
    return f"Added to {target}: {', '.join(sorted(entries))}"


def choose_skills(
    available: Mapping[str, tuple[str, ...]],
    spec: SourceSpec,
    names: Sequence[str],
    tree_hash: Callable[[str], str],
) -> dict[str, str]:
    if spec.path:
        return _skill_at_path(available, spec.path)
    if not available:
        raise SkillzError(f"no skills found in {spec.key}")
    wanted = list(names) or sorted(available)
    unknown = [name for name in wanted if name not in available]
    if unknown:
        raise SkillzError(f"not found in {spec.key}: {', '.join(unknown)}")
    return {name: _single_path(name, available[name], tree_hash) for name in wanted}


def _skill_at_path(available: Mapping[str, tuple[str, ...]], path: str) -> dict[str, str]:
    for name, paths in available.items():
        if path in paths:
            return {name: path}
    raise SkillzError(f"no skill folder (with a SKILL.md) at {path}")


def _single_path(name: str, paths: tuple[str, ...], tree_hash: Callable[[str], str]) -> str:
    """Pick one folder for a skill name. Identical copies (such as committed build output)
    resolve to the one highest in the folder hierarchy; copies that differ are an error."""
    if len(paths) == 1:
        return paths[0]
    is_one_skill = len({tree_hash(path) for path in paths}) == 1
    if not is_one_skill:
        raise SkillzError(
            f"skill {name!r} has differing copies in the repo ({', '.join(paths)}); "
            "add the one you want by its GitHub folder URL"
        )
    return min(paths, key=lambda path: (len(PurePosixPath(path).parts), path))


def _reject_existing(context: Context, chosen: Mapping[str, str], locked: Mapping[str, SkillEntry]) -> None:
    on_disk = index_skills(context)
    taken = sorted(name for name in chosen if name in locked or name in on_disk)
    if taken:
        raise SkillzError(f"already in the library: {', '.join(taken)}")


def _install_all(
    context: Context, checkout: Checkout, spec: SourceSpec, chosen: Mapping[str, str], namespace: str
) -> dict[str, SkillEntry]:
    installed: list[Path] = []
    try:
        entries = {}
        for name, path in chosen.items():
            dest = context.library / namespace / name
            if dest.exists():
                raise SkillzError(f"{dest} already exists")
            installed.append(dest)
            entries[name] = install_from_checkout(
                context, checkout, namespace=namespace, source=spec.key, path=path, dest=dest
            )
        return entries
    except BaseException:
        for folder in installed:
            shutil.rmtree(folder, ignore_errors=True)
        raise
