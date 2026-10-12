"""Write a skill folder exported from a checkout into the library, and build its lock entry."""

import shutil
from datetime import UTC, datetime
from pathlib import Path

from skillz.checkout import HEAD, Checkout, Exported
from skillz.context import Context
from skillz.copying import copy_skill
from skillz.hashing import content_hash
from skillz.lock import SkillEntry

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def install_from_checkout(
    context: Context,
    checkout: Checkout,
    *,
    namespace: str,
    source: str,
    path: str,
    dest: Path,
    rev: str = HEAD,
) -> SkillEntry:
    """Replace dest with the skill folder at path in rev, returning its lock entry."""
    write_skill_folder(context, checkout.export(path, rev), dest)
    return SkillEntry(
        namespace=namespace,
        source=source,
        path=path,
        commit=checkout.commit if rev == HEAD else rev,
        upstream_hash=checkout.tree_hash(path, rev),
        content_hash=content_hash(dest),
        installed_at=datetime.now(UTC).strftime(TIMESTAMP_FORMAT),
    )


def write_skill_folder(context: Context, exported: Exported, dest: Path) -> None:
    """Copy into a hidden staging folder first, so dest is only replaced by a complete copy."""
    staging = dest.with_name(f".{dest.name}.skillz-staging")
    shutil.rmtree(staging, ignore_errors=True)
    try:
        for warning in copy_skill(exported.folder, staging, exported.root):
            context.warn(warning)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if dest.exists():
        shutil.rmtree(dest)
    staging.rename(dest)
