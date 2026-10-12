"""Text and JSON output for skill reports."""

import json
from collections.abc import Sequence
from dataclasses import asdict

from skillz.status import SkillReport

DESCRIPTION_WIDTH = 60
NO_NAMESPACE = "-"
TABLE_HEADER = ("NAMESPACE", "NAME", "STATUS", "DESCRIPTION")


def render_json(reports: Sequence[SkillReport]) -> str:
    return json.dumps([asdict(report) for report in reports], indent=2, default=str)


def render_table(reports: Sequence[SkillReport]) -> str:
    if not reports:
        return "No skills found."
    rows = [TABLE_HEADER, *(_table_row(report) for report in reports)]
    widths = [max(len(row[column]) for row in rows) for column in range(len(TABLE_HEADER) - 1)]
    return "\n".join(_format_row(row, widths) for row in rows)


def _table_row(report: SkillReport) -> tuple[str, ...]:
    return (report.namespace or NO_NAMESPACE, report.name, report.status, _truncate(report.description))


def _format_row(row: tuple[str, ...], widths: list[int]) -> str:
    padded = [cell.ljust(width) for cell, width in zip(row, widths)]
    return "  ".join([*padded, row[-1]]).rstrip()


def _truncate(text: str) -> str:
    first_line = text.splitlines()[0] if text else ""
    is_too_long = len(first_line) > DESCRIPTION_WIDTH
    return first_line[: DESCRIPTION_WIDTH - 1] + "…" if is_too_long else first_line
