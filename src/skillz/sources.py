"""Parse source strings into specs. GitHub is the only source type for now."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from skillz.errors import SkillzError

GITHUB = "github"
VENDOR_NAMESPACE = "vendor"
NAME = r"[\w.-]+"
GITHUB_SHORTHAND = re.compile(rf"^({NAME})/({NAME})$")
GITHUB_REPO_URL = re.compile(rf"^https://github\.com/({NAME})/({NAME}?)(?:\.git)?/?$")
GITHUB_FOLDER_URL = re.compile(rf"^https://github\.com/({NAME})/({NAME})/tree/([^/]+)/(.+?)/?$")


class SourceError(SkillzError):
    pass


@dataclass(frozen=True)
class SourceSpec:
    kind: str
    owner: str
    repo: str
    ref: str | None = None
    path: str | None = None

    @property
    def key(self) -> str:
        base = f"{self.owner}/{self.repo}"
        return f"{base}@{self.ref}" if self.ref else base

    @property
    def default_namespace(self) -> str:
        return f"{VENDOR_NAMESPACE}/{self.owner}"


def parse_source(text: str) -> SourceSpec:
    candidate = text.strip()
    for parser in SOURCE_PARSERS:
        spec = parser(candidate)
        if spec:
            return spec
    raise SourceError(f"unrecognized source {text!r}; expected owner/repo or a GitHub URL")


def clone_url(spec: SourceSpec) -> str:
    return CLONE_URLS[spec.kind](spec)


def _parse_github(text: str) -> SourceSpec | None:
    if match := GITHUB_FOLDER_URL.match(text):
        owner, repo, ref, path = match.groups()
        return SourceSpec(GITHUB, owner, repo, ref=ref, path=path)
    if match := GITHUB_SHORTHAND.match(text) or GITHUB_REPO_URL.match(text):
        owner, repo = match.groups()
        return SourceSpec(GITHUB, owner, repo)
    return None


def _github_ssh_url(spec: SourceSpec) -> str:
    return f"git@github.com:{spec.owner}/{spec.repo}.git"


SOURCE_PARSERS: tuple[Callable[[str], SourceSpec | None], ...] = (_parse_github,)
CLONE_URLS: dict[str, Callable[[SourceSpec], str]] = {GITHUB: _github_ssh_url}
