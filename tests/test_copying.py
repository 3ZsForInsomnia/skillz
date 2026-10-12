import unittest

from helpers import TempDirTestCase

from skillz.copying import copy_skill


class CopySkillTest(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.root / "repo"
        self.skill = self.repo / "skills" / "pdf"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("skill")
        self.dest = self.root / "library" / "pdf"

    def test_copies_nested_files(self) -> None:
        (self.skill / "refs").mkdir()
        (self.skill / "refs" / "a.md").write_text("a")
        self.assertEqual(copy_skill(self.skill, self.dest, self.repo), [])
        self.assertEqual((self.dest / "refs" / "a.md").read_text(), "a")

    def test_symlink_inside_repo_becomes_a_real_file(self) -> None:
        (self.repo / "shared.md").write_text("shared")
        (self.skill / "shared.md").symlink_to(self.repo / "shared.md")
        copy_skill(self.skill, self.dest, self.repo)
        copied = self.dest / "shared.md"
        self.assertFalse(copied.is_symlink())
        self.assertEqual(copied.read_text(), "shared")

    def test_symlink_outside_repo_is_skipped_with_warning(self) -> None:
        (self.root / "secret.txt").write_text("nope")
        (self.skill / "leak.txt").symlink_to(self.root / "secret.txt")
        warnings = copy_skill(self.skill, self.dest, self.repo)
        self.assertFalse((self.dest / "leak.txt").exists())
        self.assertEqual(len(warnings), 1)
        self.assertIn("skills/pdf/leak.txt", warnings[0])

    def test_broken_symlink_is_skipped_with_warning(self) -> None:
        (self.skill / "gone.md").symlink_to(self.repo / "missing.md")
        self.assertEqual(len(copy_skill(self.skill, self.dest, self.repo)), 1)
        self.assertFalse((self.dest / "gone.md").exists())

    def test_symlink_to_a_parent_folder_is_skipped(self) -> None:
        (self.skill / "up").symlink_to(self.repo)
        self.assertEqual(len(copy_skill(self.skill, self.dest, self.repo)), 1)
        self.assertFalse((self.dest / "up").exists())


if __name__ == "__main__":
    unittest.main()
