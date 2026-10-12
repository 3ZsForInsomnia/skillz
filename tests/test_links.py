import json
import unittest

from helpers import FakeTerminal, TempDirTestCase, run_cli, write_skill


class LinkToTest(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.library = self.root / "library"
        self.link = self.root / "claude" / "skills"
        self.terminal = FakeTerminal()

    def list_skills(self) -> tuple[int, str]:
        context = self.terminal.context(self.library, namespaces={"core": {"link_to": str(self.link)}})
        code, out, _ = run_cli("list", "-j", context=context)
        return code, out

    def test_any_command_creates_the_link_and_namespace_folder(self) -> None:
        self.list_skills()
        self.assertTrue(self.link.is_symlink())
        self.assertEqual(self.link.resolve(), (self.library / "core").resolve())
        self.assertEqual(self.terminal.warnings, [f"linked {self.link} -> {self.library / 'core'}"])

    def test_skills_in_the_namespace_are_visible_through_the_link(self) -> None:
        write_skill(self.library, "core", "lbm")
        self.list_skills()
        self.assertTrue((self.link / "lbm" / "SKILL.md").is_file())

    def test_link_messages_stay_out_of_json_output(self) -> None:
        code, out = self.list_skills()
        self.assertEqual((code, json.loads(out)), (0, []))

    def test_correct_link_is_left_quietly(self) -> None:
        self.list_skills()
        self.terminal.warnings.clear()
        self.list_skills()
        self.assertEqual(self.terminal.warnings, [])

    def test_existing_folder_is_never_replaced(self) -> None:
        self.link.mkdir(parents=True)
        (self.link / "keep.md").write_text("mine")
        self.list_skills()
        self.assertFalse(self.link.is_symlink())
        self.assertEqual((self.link / "keep.md").read_text(), "mine")
        self.assertIn("isn't a link to", self.terminal.warnings[0])

    def test_link_pointing_elsewhere_is_left_with_a_warning(self) -> None:
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.link.parent.mkdir(parents=True)
        self.link.symlink_to(elsewhere)
        code, _ = self.list_skills()
        self.assertEqual(code, 0)
        self.assertEqual(self.link.resolve(), elsewhere.resolve())
        self.assertIn(f"links to {elsewhere}", self.terminal.warnings[0])


if __name__ == "__main__":
    unittest.main()
