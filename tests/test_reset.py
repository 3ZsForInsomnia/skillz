import shutil
import unittest

from helpers import InstalledSourceTestCase, skill_file, write_skill


class ResetCommandTest(InstalledSourceTestCase):
    def test_restores_edited_skill(self) -> None:
        self.edit_local("pdf", "mine")
        code, out, _ = self.cli("reset", "pdf")
        self.assertEqual(code, 0)
        self.assertRegex(out, r"^pdf: reset to [0-9a-f]{12}\n$")
        self.assertEqual(self.local_text("pdf"), skill_file("pdf"))
        self.assertEqual(self.statuses()["pdf"], ("vendor/acme", "unchanged"))

    def test_restores_locked_version_even_after_upstream_moves_on(self) -> None:
        self.edit_upstream("skills/pdf/SKILL.md", "newer")
        self.edit_local("pdf", "mine")
        self.cli("reset", "pdf")
        self.assertEqual(self.local_text("pdf"), skill_file("pdf"))
        self.assertEqual(self.cli("status")[1], "pdf (vendor/acme): update available\n")

    def test_restores_missing_skill_into_its_locked_namespace(self) -> None:
        shutil.rmtree(self.library / "vendor")
        self.cli("reset", "pdf")
        self.assertEqual(self.local_text("pdf"), skill_file("pdf"))

    def test_extra_files_added_locally_are_removed(self) -> None:
        (self.library / "vendor/acme/pdf/notes.md").write_text("scratch")
        self.cli("reset", "pdf")
        self.assertFalse((self.library / "vendor/acme/pdf/notes.md").exists())

    def test_requires_names(self) -> None:
        with self.assertRaises(SystemExit):
            self.cli("reset")

    def test_rejects_untracked_skill(self) -> None:
        write_skill(self.library, "custom", "mine")
        code, _, err = self.cli("reset", "mine")
        self.assertEqual(code, 1)
        self.assertIn("not tracked by skillz: mine", err)


if __name__ == "__main__":
    unittest.main()
