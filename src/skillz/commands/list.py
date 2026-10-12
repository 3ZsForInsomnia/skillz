"""skillz list: every skill in the library, and in pulled folders, with its status."""

from skillz.catalog import all_skills
from skillz.context import Context
from skillz.hashing import content_hash
from skillz.lock import load_lock
from skillz.render import render_json, render_table
from skillz.status import build_reports


def run_list(context: Context, as_json: bool) -> str:
    lock = load_lock(context.library)
    reports = build_reports(all_skills(context), lock, content_hash)
    return render_json(reports) if as_json else render_table(reports)
