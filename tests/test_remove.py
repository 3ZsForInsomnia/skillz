import unittest

from helpers import FakeTerminal, TempDirTestCase, make_source_repo, read_lock, run_cli, skill_file, write_skill


class RemoveCommandTest(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.library = self.root / "library"
        repo = make_source_repo(
            self.root / "source",
            {"skills/pdf/SKILL.md": skill_file("pdf"), "skills/docx/SKILL.md": skill_file("docx")},
        )
        run_cli("add", "acme/skills", context=FakeTerminal().context(self.library, repo))

    def remove(self, *names: str, terminal: FakeTerminal) -> tuple[int, str, str]:
        return run_cli("remove", *names, context=terminal.context(self.library))

    def test_confirmed_removal_deletes_folder_and_lock_entry(self) -> None:
        code, out, _ = self.remove("pdf", terminal=FakeTerminal(True))
        self.assertEqual((code, out), (0, "Removed: pdf\n"))
        self.assertFalse((self.library / "vendor/acme/pdf").exists())
        lock = read_lock(self.library)
        self.assertEqual(set(lock["skills"]), {"docx"})
        self.assertEqual(lock["sources"]["acme/skills"]["skills"], ["docx"])

    def test_removing_last_skill_of_a_source_drops_the_source(self) -> None:
        self.remove("pdf", "docx", terminal=FakeTerminal(True))
        self.assertEqual(read_lock(self.library)["sources"], {})

    def test_declining_keeps_everything(self) -> None:
        code, out, _ = self.remove("pdf", terminal=FakeTerminal(False))
        self.assertEqual((code, out), (0, "Cancelled.\n"))
        self.assertTrue((self.library / "vendor/acme/pdf").is_dir())
        self.assertIn("pdf", read_lock(self.library)["skills"])

    def test_question_names_skills_and_flags_local_edits(self) -> None:
        (self.library / "vendor/acme/pdf/SKILL.md").write_text("edited")
        terminal = FakeTerminal(False)
        self.remove("pdf", "docx", terminal=terminal)
        self.assertEqual(
            terminal.questions, ["Remove pdf, docx? These have local edits that will be lost: pdf."]
        )

    def test_rejects_untracked_skills(self) -> None:
        write_skill(self.library, "custom", "mine")
        code, _, err = self.remove("mine", terminal=FakeTerminal())
        self.assertEqual(code, 1)
        self.assertIn("not tracked by skillz", err)
        self.assertTrue((self.library / "custom/mine").is_dir())

    def test_skill_missing_from_disk_is_dropped_from_lock(self) -> None:
        (self.library / "vendor/acme/pdf/SKILL.md").unlink()
        (self.library / "vendor/acme/pdf").rmdir()
        self.remove("pdf", terminal=FakeTerminal(True))
        self.assertNotIn("pdf", read_lock(self.library)["skills"])

    def test_repeated_name_is_removed_once(self) -> None:
        code, out, _ = self.remove("pdf", "pdf", terminal=FakeTerminal(True))
        self.assertEqual((code, out), (0, "Removed: pdf\n"))


if __name__ == "__main__":
    unittest.main()
