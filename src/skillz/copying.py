"""Copy skill folders out of a checkout, replacing symlinks with the files they point to."""

import shutil
from pathlib import Path


def copy_skill(source: Path, dest: Path, repo_root: Path) -> list[str]:
    """Copy source to dest and return a warning for each symlink that was skipped."""
    dest.mkdir(parents=True)
    warnings: list[str] = []
    for entry in sorted(source.iterdir()):
        if entry.is_symlink() and not _is_safe_link(entry, repo_root):
            warnings.append(f"skipped symlink {entry.relative_to(repo_root)}: target is missing or outside the skill")
        elif entry.is_dir():
            warnings.extend(copy_skill(entry, dest / entry.name, repo_root))
        else:
            shutil.copy2(entry, dest / entry.name)
    return warnings


def _is_safe_link(link: Path, repo_root: Path) -> bool:
    target = link.resolve()
    is_inside_repo = target.is_relative_to(repo_root.resolve())
    points_to_ancestor = link.parent.resolve().is_relative_to(target)
    return target.exists() and is_inside_repo and not points_to_ancestor
