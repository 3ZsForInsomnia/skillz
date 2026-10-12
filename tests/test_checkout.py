import unittest

from helpers import TempDirTestCase, commit_all, git, make_source_repo, skill_file

from skillz.checkout import find_skill_paths, open_checkout
from skillz.errors import SkillzError


class FindSkillPathsTest(unittest.TestCase):
    def test_each_skill_folder_is_named_after_its_folder(self) -> None:
        files = ["README.md", "skills/pdf/SKILL.md", "skills/pdf/ref.md", "other/docx/SKILL.md"]
        self.assertEqual(
            find_skill_paths(files, "repo"),
            {"docx": ("other/docx",), "pdf": ("skills/pdf",)},
        )

    def test_skills_nested_inside_a_skill_are_ignored(self) -> None:
        files = ["skills/pdf/SKILL.md", "skills/pdf/examples/demo/SKILL.md"]
        self.assertEqual(find_skill_paths(files, "repo"), {"pdf": ("skills/pdf",)})

    def test_repo_root_skill_is_named_after_the_repo(self) -> None:
        files = ["SKILL.md", "examples/x/SKILL.md"]
        self.assertEqual(find_skill_paths(files, "humanizer"), {"humanizer": ("",)})

    def test_same_name_in_two_places_keeps_both_paths(self) -> None:
        files = ["a/pdf/SKILL.md", "b/pdf/SKILL.md"]
        self.assertEqual(find_skill_paths(files, "repo"), {"pdf": ("a/pdf", "b/pdf")})


class OpenCheckoutTest(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.repo = make_source_repo(
            self.root / "source",
            {"skills/pdf/SKILL.md": skill_file("pdf"), "skills/docx/SKILL.md": skill_file("docx")},
        )

    def test_lists_skills_and_commit(self) -> None:
        with open_checkout(f"file://{self.repo}", None, "source") as checkout:
            self.assertEqual(set(checkout.skill_paths), {"pdf", "docx"})
            self.assertEqual(checkout.commit, git(self.repo, "rev-parse", "HEAD").strip())

    def test_tree_hash_matches_upstream_folder(self) -> None:
        with open_checkout(f"file://{self.repo}", None, "source") as checkout:
            self.assertEqual(checkout.tree_hash("skills/pdf"), git(self.repo, "rev-parse", "HEAD:skills/pdf").strip())

    def test_export_writes_only_the_requested_folder(self) -> None:
        with open_checkout(f"file://{self.repo}", None, "source") as checkout:
            exported = checkout.export("skills/pdf")
            self.assertEqual((exported.folder / "SKILL.md").read_text(), skill_file("pdf"))
            self.assertFalse((exported.root / "skills/docx").exists())

    def test_export_at_an_older_commit(self) -> None:
        old_commit = git(self.repo, "rev-parse", "HEAD").strip()
        (self.repo / "skills/pdf/SKILL.md").write_text("newer")
        commit_all(self.repo)
        with open_checkout(f"file://{self.repo}", None, "source") as checkout:
            checkout.fetch_commit(old_commit)
            self.assertEqual((checkout.export("skills/pdf", old_commit).folder / "SKILL.md").read_text(), skill_file("pdf"))
            self.assertEqual((checkout.export("skills/pdf").folder / "SKILL.md").read_text(), "newer")

    def test_fetching_an_unknown_commit_is_a_clear_error(self) -> None:
        with open_checkout(f"file://{self.repo}", None, "source") as checkout:
            with self.assertRaisesRegex(SkillzError, "no longer available upstream"):
                checkout.fetch_commit("0" * 40)

    def test_has_path_reports_missing_folders(self) -> None:
        with open_checkout(f"file://{self.repo}", None, "source") as checkout:
            self.assertTrue(checkout.has_path("skills/pdf"))
            self.assertFalse(checkout.has_path("skills/gone"))

    def test_clone_is_deleted_afterwards(self) -> None:
        with open_checkout(f"file://{self.repo}", None, "source") as checkout:
            root = checkout.root
        self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
