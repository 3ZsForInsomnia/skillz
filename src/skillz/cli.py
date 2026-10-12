"""Command-line entry point."""

import argparse
import sys

from skillz import paths
from skillz.commands.add import run_add
from skillz.commands.list import run_list
from skillz.commands.move import run_move
from skillz.commands.remove import run_remove
from skillz.commands.reset import run_reset
from skillz.commands.status import run_status
from skillz.commands.update import run_update
from skillz.context import Context, confirm_on_terminal, warn_on_stderr
from skillz.errors import SkillzError
from skillz.links import sync_links
from skillz.manifest import load_manifest
from skillz.sources import clone_url


def main(argv: list[str] | None = None, context: Context | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        context = context or default_context()
        sync_links(context)
        output = args.handler(context, args)
    except SkillzError as error:
        print(f"skillz: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


def default_context() -> Context:
    manifest = load_manifest(paths.manifest_path())
    return Context(
        library=manifest.library,
        confirm=confirm_on_terminal,
        clone_url=clone_url,
        warn=warn_on_stderr,
        namespaces=manifest.namespaces,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillz",
        description="Download, track, and organize agent skills in a namespaced local library.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    for add_command in (_add_list, _add_add, _add_remove, _add_move, _add_status, _add_update, _add_reset):
        add_command(commands)
    return parser


def _add_list(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("list", help="list every skill in the library with its status")
    command.add_argument("-j", "--json", action="store_true", help="print JSON instead of a table")
    command.set_defaults(handler=lambda context, args: run_list(context, args.json))


def _add_add(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("add", help="download skills from a source into the library")
    command.add_argument("source", help="owner/repo, or a GitHub URL to a repo or a skill folder")
    command.add_argument("names", nargs="*", help="skills to install; all skills in the repo if omitted")
    command.add_argument("-n", "--namespace", help="namespace to install into (default: vendor/<owner>)")
    command.set_defaults(handler=lambda context, args: run_add(context, args.source, args.names, args.namespace))


def _add_remove(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("remove", help="delete tracked skills and drop them from the lock")
    command.add_argument("names", nargs="+", help="skills to remove")
    command.set_defaults(handler=lambda context, args: run_remove(context, args.names))


def _add_move(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("move", help="move a skill to another namespace")
    command.add_argument("name", help="skill to move")
    command.add_argument("namespace", help="namespace to move it into")
    command.set_defaults(handler=lambda context, args: run_move(context, args.name, args.namespace))


def _add_status(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("status", help="show tracked skills with local edits or upstream updates")
    command.add_argument("names", nargs="*", help="skills to check; all tracked skills if omitted")
    command.add_argument("-d", "--diff", action="store_true", help="show a git diff for each change")
    command.set_defaults(handler=lambda context, args: run_status(context, args.names, args.diff))


def _add_update(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("update", help="replace tracked skills with their upstream versions")
    command.add_argument("names", nargs="*", help="skills to update; all tracked skills if omitted")
    command.add_argument("-c", "--check", action="store_true", help="only report available updates")
    command.add_argument(
        "-f", "--force", action="store_true", help="overwrite local edits (requires skill names)"
    )
    command.set_defaults(handler=lambda context, args: run_update(context, args.names, args.check, args.force))


def _add_reset(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("reset", help="restore skills to exactly what the lock records")
    command.add_argument("names", nargs="+", help="skills to reset")
    command.set_defaults(handler=lambda context, args: run_reset(context, args.names))
