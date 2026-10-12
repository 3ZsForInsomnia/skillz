import unittest

from helpers import TempDirTestCase, write_skill

from skillz.hashing import content_hash


class ContentHashTest(TempDirTestCase):
    def test_identical_folders_hash_the_same(self) -> None:
        first = write_skill(self.root, "a", "pdf")
        second = write_skill(self.root, "b", "pdf")
        self.assertEqual(content_hash(first), content_hash(second))

    def test_hash_is_prefixed_with_algorithm(self) -> None:
        self.assertRegex(content_hash(write_skill(self.root, "a", "pdf")), r"^sha256:[0-9a-f]{64}$")

    def test_editing_a_file_changes_the_hash(self) -> None:
        folder = write_skill(self.root, "a", "pdf")
        before = content_hash(folder)
        (folder / "SKILL.md").write_text("edited")
        self.assertNotEqual(content_hash(folder), before)

    def test_adding_a_nested_file_changes_the_hash(self) -> None:
        folder = write_skill(self.root, "a", "pdf")
        before = content_hash(folder)
        (folder / "references").mkdir()
        (folder / "references" / "notes.md").write_text("notes")
        self.assertNotEqual(content_hash(folder), before)

    def test_renaming_a_file_changes_the_hash(self) -> None:
        folder = write_skill(self.root, "a", "pdf")
        (folder / "one.md").write_text("same")
        before = content_hash(folder)
        (folder / "one.md").rename(folder / "two.md")
        self.assertNotEqual(content_hash(folder), before)

    def test_moving_bytes_between_files_changes_the_hash(self) -> None:
        folder = write_skill(self.root, "a", "pdf")
        (folder / "a.md").write_text("xy")
        (folder / "b.md").write_text("z")
        before = content_hash(folder)
        (folder / "a.md").write_text("x")
        (folder / "b.md").write_text("yz")
        self.assertNotEqual(content_hash(folder), before)

    def test_ds_store_is_ignored(self) -> None:
        folder = write_skill(self.root, "a", "pdf")
        before = content_hash(folder)
        (folder / ".DS_Store").write_bytes(b"\x00junk")
        self.assertEqual(content_hash(folder), before)


if __name__ == "__main__":
    unittest.main()
