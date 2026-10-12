import unittest
from pathlib import Path

from helpers import TempDirTestCase, lock_entry, write_lock, write_skill

from skillz.library import scan_library
from skillz.lock import load_lock
from skillz.status import build_reports


def fake_hash(path: Path) -> str:
    return f"sha256:{path.name}"


class BuildReportsTest(TempDirTestCase):
    def statuses(self) -> dict[str, str]:
        reports = build_reports(scan_library(self.root), load_lock(self.root), fake_hash)
        return {report.name: report.status for report in reports}

    def test_skill_not_in_lock_is_untracked(self) -> None:
        write_skill(self.root, "custom", "lbm")
        self.assertEqual(self.statuses(), {"lbm": "untracked"})

    def test_matching_hash_is_unchanged(self) -> None:
        write_skill(self.root, "vendor/acme", "pdf")
        write_lock(self.root, {"pdf": lock_entry("vendor/acme", content_hash="sha256:pdf")})
        self.assertEqual(self.statuses(), {"pdf": "unchanged"})

    def test_different_hash_is_edited(self) -> None:
        write_skill(self.root, "vendor/acme", "pdf")
        write_lock(self.root, {"pdf": lock_entry("vendor/acme", content_hash="sha256:other")})
        self.assertEqual(self.statuses(), {"pdf": "edited"})

    def test_skill_outside_its_locked_namespace_is_misplaced(self) -> None:
        write_skill(self.root, "core", "pdf")
        write_lock(self.root, {"pdf": lock_entry("vendor/acme", content_hash="sha256:pdf")})
        self.assertEqual(self.statuses(), {"pdf": "misplaced"})

    def test_locked_skill_without_folder_is_missing(self) -> None:
        write_lock(self.root, {"pdf": lock_entry("vendor/acme")})
        reports = build_reports(scan_library(self.root), load_lock(self.root), fake_hash)
        self.assertEqual(
            [(r.name, r.namespace, r.status, r.path) for r in reports],
            [("pdf", "vendor/acme", "missing", None)],
        )

    def test_untracked_skills_are_not_hashed(self) -> None:
        write_skill(self.root, "custom", "lbm")

        def failing_hash(path: Path) -> str:
            raise AssertionError(f"hashed {path}")

        build_reports(scan_library(self.root), load_lock(self.root), failing_hash)

    def test_reports_include_source_for_tracked_skills(self) -> None:
        write_skill(self.root, "vendor/acme", "pdf")
        write_skill(self.root, "custom", "lbm")
        write_lock(self.root, {"pdf": lock_entry("vendor/acme", source="acme/skills")})
        reports = build_reports(scan_library(self.root), load_lock(self.root), fake_hash)
        self.assertEqual({r.name: r.source for r in reports}, {"lbm": None, "pdf": "acme/skills"})


if __name__ == "__main__":
    unittest.main()
