"""Minimal SKILL.md frontmatter reader for top-level string fields.

Handles plain, quoted, multi-line, and block (| or >) scalars. Nested values such as
mappings or lists read as an empty string; unknown fields are never an error.
"""

import re
from collections.abc import Iterator

DELIMITER = "---"
KEY_LINE = re.compile(r"^([A-Za-z0-9_-]+):[ \t]*(.*)$")
BLOCK_INDICATOR = re.compile(r"^[|>][-+0-9]*$")
NESTED_START = re.compile(r"^(- |[A-Za-z0-9_-]+:)")


def read_frontmatter(text: str) -> dict[str, str]:
    return {key: _field_value(inline, rest) for key, inline, rest in _fields(_block_lines(text))}


def _block_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != DELIMITER:
        return []
    closing = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == DELIMITER), None)
    return lines[1:closing] if closing else []


def _fields(lines: list[str]) -> Iterator[tuple[str, str, list[str]]]:
    key, inline, rest = None, "", []
    for line in lines:
        match = KEY_LINE.match(line)
        if match:
            if key:
                yield key, inline, rest
            key, inline, rest = match[1], match[2].strip(), []
        elif key and _is_continuation(line):
            rest.append(line)
    if key:
        yield key, inline, rest


def _is_continuation(line: str) -> bool:
    return line.startswith((" ", "\t")) or not line.strip()


def _field_value(inline: str, rest: list[str]) -> str:
    stripped = [line.strip() for line in rest]
    if BLOCK_INDICATOR.match(inline):
        return _literal(stripped) if inline.startswith("|") else _fold(stripped)
    if not inline and _starts_nested(stripped):
        return ""
    return _unquote(_fold([inline, *stripped]))


def _starts_nested(lines: list[str]) -> bool:
    first = next((line for line in lines if line), "")
    return bool(NESTED_START.match(first))


def _literal(lines: list[str]) -> str:
    return "\n".join(lines).strip()


def _fold(lines: list[str]) -> str:
    paragraphs = " ".join(line or "\n" for line in lines)
    return re.sub(r" ?\n ?", "\n", paragraphs).strip()


def _unquote(value: str) -> str:
    is_quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
    if not is_quoted:
        return value
    inner = value[1:-1]
    return inner.replace("''", "'") if value[0] == "'" else inner.replace('\\"', '"').replace("\\\\", "\\")
