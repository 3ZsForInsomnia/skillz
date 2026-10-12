"""Command-line entry point."""

import argparse
import sys

from skillz import paths
from skillz.hashing import content_hash
from skillz.library import scan_library
from skillz.lock import LockError, load_lock
from skillz.manifest import ManifestError, load_manifest
from skillz.render import render_json, render_table
from skillz.status import SkillReport, build_reports

USER_ERRORS = (ManifestError, LockError)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = args.handler(args)
    except USER_ERRORS as error:
        print(f"skillz: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillz",
        description="Download, track, and organize agent skills in a namespaced local library.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    _add_list_command(commands)
    return parser


def _add_list_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser("list", help="list every skill in the library with its status")
    command.add_argument("-j", "--json", action="store_true", help="print JSON instead of a table")
    command.set_defaults(handler=run_list)


def run_list(args: argparse.Namespace) -> str:
    reports = load_reports()
    return render_json(reports) if args.json else render_table(reports)


def load_reports() -> list[SkillReport]:
    manifest = load_manifest(paths.manifest_path())
    lock = load_lock(manifest.library)
    return build_reports(scan_library(manifest.library), lock, content_hash)
