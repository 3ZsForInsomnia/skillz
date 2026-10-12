import shutil
import unittest

from helpers import InstalledSourceTestCase, commit_all


class StatusCommandTest(InstalledSourceTestCase):
    def test_clean_library_is_all_clear(self) -> None:
        self.assertEqual(self.cli("status"), (0, "Everything is up to date.\n", ""))

    def test_reports_local_edits(self) -> None:
        self.edit_local("pdf", "mine")
        self.assertEqual(self.cli("status")[1], "pdf (vendor/acme): local edits\n")

    def test_reports_available_updates(self) -> None:
        self.edit_upstream("skills/docx/SKILL.md", "newer")
        self.assertEqual(self.cli("status")[1], "docx (vendor/acme): update available\n")

    def test_reports_edits_and_update_together(self) -> None:
        self.edit_local("pdf", "mine")
        self.edit_upstream("skills/pdf/SKILL.md", "newer")
        self.assertEqual(self.cli("status")[1], "pdf (vendor/acme): local edits, update available\n")

    def test_reports_missing_local_folder(self) -> None:
        shutil.rmtree(self.library / "vendor/acme/pdf")
        self.assertEqual(self.cli("status")[1], "pdf (vendor/acme): missing locally\n")

    def test_reports_skill_removed_upstream(self) -> None:
        shutil.rmtree(self.repo / "skills/docx")
        commit_all(self.repo)
        self.assertEqual(self.cli("status")[1], "docx (vendor/acme): removed upstream\n")

    def test_names_limit_the_check(self) -> None:
        self.edit_local("pdf", "mine")
        self.assertEqual(self.cli("status", "docx")[1], "Everything is up to date.\n")

    def test_rejects_untracked_names(self) -> None:
        code, _, err = self.cli("status", "nope")
        self.assertEqual(code, 1)
        self.assertIn("not tracked by skillz: nope", err)

    def test_diff_shows_local_edits_against_locked_version(self) -> None:
        self.edit_local("pdf", "mine\n")
        out = self.cli("status", "-d")[1]
        self.assertIn("--- locked/pdf/SKILL.md", out)
        self.assertIn("+++ local/pdf/SKILL.md", out)
        self.assertIn("+mine", out)

    def test_diff_shows_what_an_update_would_change(self) -> None:
        self.edit_upstream("skills/docx/SKILL.md", "newer\n")
        out = self.cli("status", "-d")[1]
        self.assertIn("--- local/docx/SKILL.md", out)
        self.assertIn("+++ upstream/docx/SKILL.md", out)
        self.assertIn("+newer", out)


if __name__ == "__main__":
    unittest.main()
