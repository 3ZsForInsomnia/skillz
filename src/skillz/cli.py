"""Command-line entry point."""

import argparse
import sys

from skillz import paths
from skillz.commands.add import run_add
from skillz.commands.list import run_list
from skillz.commands.move import run_move
from skillz.commands.remove import run_remove
from skillz.context import Context, confirm_on_terminal, warn_on_stderr
from skillz.errors import SkillzError
from skillz.manifest import load_manifest
from skillz.sources import clone_url


def main(argv: list[str] | None = None, context: Context | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = args.handler(context or default_context(), args)
    except SkillzError as error:
        print(f"skillz: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


def default_context() -> Context:
    manifest = load_manifest(paths.manifest_path())
    return Context(library=manifest.library, confirm=confirm_on_terminal, clone_url=clone_url, warn=warn_on_stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillz",
        description="Download, track, and organize agent skills in a namespaced local library.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    for add_command in (_add_list, _add_add, _add_remove, _add_move):
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
