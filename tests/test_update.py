import shutil
import unittest

from helpers import InstalledSourceTestCase, commit_all, git, read_lock


class UpdateCommandTest(InstalledSourceTestCase):
    def test_nothing_to_update_is_all_clear(self) -> None:
        self.assertEqual(self.cli("update"), (0, "Everything is up to date.\n", ""))

    def test_replaces_skill_and_records_new_commit(self) -> None:
        self.edit_upstream("skills/pdf/SKILL.md", "newer")
        self.assertEqual(self.cli("update")[1], "pdf: updated\n")
        self.assertEqual(self.local_text("pdf"), "newer")
        self.assertEqual(read_lock(self.library)["skills"]["pdf"]["commit"], git(self.repo, "rev-parse", "HEAD").strip())
        self.assertEqual(self.statuses()["pdf"], ("vendor/acme", "unchanged"))
        self.assertEqual(self.cli("status")[1], "Everything is up to date.\n")

    def test_check_only_reports_without_changing_anything(self) -> None:
        self.edit_upstream("skills/pdf/SKILL.md", "newer")
        self.assertEqual(self.cli("update", "-c")[1], "pdf: update available\n")
        self.assertNotEqual(self.local_text("pdf"), "newer")

    def test_skips_edited_skills_without_force(self) -> None:
        self.edit_local("pdf", "mine")
        self.edit_upstream("skills/pdf/SKILL.md", "newer")
        self.assertIn("pdf: skipped, has local edits", self.cli("update")[1])
        self.assertEqual(self.local_text("pdf"), "mine")

    def test_force_with_a_name_overwrites_edits(self) -> None:
        self.edit_local("pdf", "mine")
        self.edit_upstream("skills/pdf/SKILL.md", "newer")
        self.assertEqual(self.cli("update", "pdf", "-f")[1], "pdf: updated\n")
        self.assertEqual(self.local_text("pdf"), "newer")

    def test_force_without_names_is_refused(self) -> None:
        self.edit_local("pdf", "mine")
        self.edit_upstream("skills/pdf/SKILL.md", "newer")
        code, _, err = self.cli("update", "-f")
        self.assertEqual(code, 1)
        self.assertIn("needs skill names", err)
        self.assertEqual(self.local_text("pdf"), "mine")

    def test_skill_removed_upstream_is_left_alone(self) -> None:
        shutil.rmtree(self.repo / "skills/docx")
        commit_all(self.repo)
        self.assertEqual(self.cli("update")[1], "docx: removed upstream; left as is\n")
        self.assertTrue((self.library / "vendor/acme/docx").is_dir())

    def test_updates_a_moved_skill_where_it_lives(self) -> None:
        (self.library / "core").mkdir()
        self.cli("move", "pdf", "core")
        self.edit_upstream("skills/pdf/SKILL.md", "newer")
        self.cli("update")
        self.assertEqual(self.local_text("pdf", "core"), "newer")


if __name__ == "__main__":
    unittest.main()
