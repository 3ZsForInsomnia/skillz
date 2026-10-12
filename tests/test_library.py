import unittest

from helpers import TempDirTestCase, write_skill

from skillz.library import scan_library


def names_by_namespace(skills) -> list[tuple[str, str]]:
    return [(skill.namespace, skill.name) for skill in skills]


class ScanLibraryTest(TempDirTestCase):
    def test_missing_library_has_no_skills(self) -> None:
        self.assertEqual(scan_library(self.root / "absent"), [])

    def test_namespace_is_the_folder_path_above_the_skill(self) -> None:
        write_skill(self.root, "custom", "lbm")
        write_skill(self.root, "vendor/anthropics", "pdf")
        self.assertEqual(
            names_by_namespace(scan_library(self.root)),
            [("custom", "lbm"), ("vendor/anthropics", "pdf")],
        )

    def test_reads_description_from_frontmatter(self) -> None:
        write_skill(self.root, "custom", "lbm", description="Offload bulk text work.")
        self.assertEqual(scan_library(self.root)[0].description, "Offload bulk text work.")

    def test_folders_inside_a_skill_are_not_skills(self) -> None:
        folder = write_skill(self.root, "custom", "outer")
        write_skill(folder, "examples", "inner")
        self.assertEqual(names_by_namespace(scan_library(self.root)), [("custom", "outer")])

    def test_skill_at_library_root_has_empty_namespace(self) -> None:
        write_skill(self.root, "", "loose")
        self.assertEqual(names_by_namespace(scan_library(self.root)), [("", "loose")])

    def test_skill_file_in_library_root_itself_is_ignored(self) -> None:
        (self.root / "SKILL.md").write_text("---\nname: root\n---\n")
        self.assertEqual(scan_library(self.root), [])

    def test_hidden_folders_are_skipped(self) -> None:
        write_skill(self.root, ".git", "not-a-skill")
        self.assertEqual(scan_library(self.root), [])

    def test_follows_symlinked_namespace_folder(self) -> None:
        elsewhere = self.root / "elsewhere"
        write_skill(elsewhere, "", "shared")
        library = self.root / "library"
        library.mkdir()
        (library / "linked").symlink_to(elsewhere)
        self.assertEqual(names_by_namespace(scan_library(library)), [("linked", "shared")])

    def test_symlink_loop_does_not_hang(self) -> None:
        write_skill(self.root, "custom", "lbm")
        (self.root / "custom" / "loop").symlink_to(self.root)
        self.assertEqual(names_by_namespace(scan_library(self.root)), [("custom", "lbm")])


if __name__ == "__main__":
    unittest.main()
