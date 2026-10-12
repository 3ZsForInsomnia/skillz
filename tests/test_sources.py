import unittest

from skillz.errors import SkillzError
from skillz.sources import clone_url, parse_source


class ParseSourceTest(unittest.TestCase):
    def test_shorthand_is_repo_default_branch(self) -> None:
        spec = parse_source("anthropics/skills")
        self.assertEqual((spec.owner, spec.repo, spec.ref, spec.path), ("anthropics", "skills", None, None))
        self.assertEqual(spec.key, "anthropics/skills")

    def test_repo_url_matches_shorthand(self) -> None:
        for url in ("https://github.com/anthropics/skills", "https://github.com/anthropics/skills.git/"):
            with self.subTest(url=url):
                self.assertEqual(parse_source(url), parse_source("anthropics/skills"))

    def test_folder_url_pins_ref_and_path(self) -> None:
        spec = parse_source("https://github.com/softaworks/agent-toolkit/tree/main/skills/humanizer/")
        self.assertEqual((spec.ref, spec.path), ("main", "skills/humanizer"))
        self.assertEqual(spec.key, "softaworks/agent-toolkit@main")

    def test_default_namespace_is_vendor_owner(self) -> None:
        self.assertEqual(parse_source("anthropics/skills").default_namespace, "vendor/anthropics")

    def test_clones_over_ssh(self) -> None:
        self.assertEqual(clone_url(parse_source("anthropics/skills")), "git@github.com:anthropics/skills.git")

    def test_rejects_unrecognized_source(self) -> None:
        for text in ("just-a-name", "https://gitlab.com/a/b", "a/b/c"):
            with self.subTest(text=text), self.assertRaisesRegex(SkillzError, "unrecognized source"):
                parse_source(text)


if __name__ == "__main__":
    unittest.main()
