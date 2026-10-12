import shutil
import subprocess
import unittest

from helpers import FakeTerminal, InstalledSourceTestCase, run_cli, write_skill

from skillz.cli import build_parser


class CompletionHelpersTest(InstalledSourceTestCase):
    def setUp(self) -> None:
        super().setUp()
        write_skill(self.library, "custom", "lbm")
        self.work = self.root / "work"
        write_skill(self.work, "", "deploy")

    def cli_with_pull(self, *argv: str) -> str:
        namespaces = {"work": {"pull_from": str(self.work)}, "core": {}}
        return run_cli(*argv, context=FakeTerminal().context(self.library, self.repo, namespaces))[1]

    def test_names_lists_every_skill(self) -> None:
        self.assertEqual(self.cli_with_pull("_names").split(), ["deploy", "docx", "lbm", "pdf"])

    def test_managed_names_leave_out_external_skills(self) -> None:
        self.assertEqual(self.cli_with_pull("_names", "--managed").split(), ["docx", "lbm", "pdf"])

    def test_tracked_names_are_only_locked_skills(self) -> None:
        self.assertEqual(self.cli_with_pull("_names", "--tracked").split(), ["docx", "pdf"])

    def test_namespaces_include_folders_and_configured_ones_but_not_pulled(self) -> None:
        self.assertEqual(self.cli_with_pull("_namespaces").split(), ["core", "custom", "vendor", "vendor/acme"])

    def test_helpers_are_hidden_from_help(self) -> None:
        help_text = build_parser().format_help()
        self.assertIn("completions", help_text)
        self.assertNotIn("_names", help_text)


class CompletionScriptTest(InstalledSourceTestCase):
    def script(self) -> str:
        return self.cli("completions")[1]

    def test_script_is_valid_zsh(self) -> None:
        if shutil.which("zsh") is None:
            self.skipTest("zsh is not installed")
        result = subprocess.run(["zsh", "-n"], input=self.script(), capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stderr), (0, ""))

    def test_name_helper_ignores_options_added_by_zsh(self) -> None:
        if shutil.which("zsh") is None:
            self.skipTest("zsh is not installed")
        helpers_only = self.script().split("\n_skillz() {")[0].removeprefix("#compdef skillz\n")
        calls = self.root / "skillz-calls"
        driver = (
            f'skillz() {{ print -r -- "skillz $*" >> {calls}; print -l pdf lbm; }}\n'
            '_describe() { print -r -- "describe $1 ${(j: :)${(P)2}} ${(j: :)@[3,-1]}"; }\n'
            f"{helpers_only}\n"
            "_skillz_names -J -default- --managed\n"
        )
        result = subprocess.run(["zsh", "-f"], input=driver, capture_output=True, text=True)
        self.assertEqual(calls.read_text(), "skillz _names --managed\n")
        self.assertEqual(result.stdout, "describe skill pdf lbm -J -default-\n")

    def test_lists_visible_commands_with_their_help(self) -> None:
        script = self.script()
        self.assertTrue(script.startswith("#compdef skillz\n"))
        self.assertIn("'move:move a skill to another namespace'", script)
        self.assertNotIn("'_names:", script)

    def test_arguments_complete_from_the_right_source(self) -> None:
        script = self.script()
        self.assertIn("'1:name:_skillz_names --managed'", script)
        self.assertIn("'2:namespace:_skillz_namespaces'", script)
        self.assertIn("'*:names:_skillz_names --tracked'", script)
        self.assertIn("{-n,--namespace}'[namespace to install into (default: vendor/<owner>)]:namespace:_skillz_namespaces'", script)

    def test_flags_list_short_and_long_forms(self) -> None:
        self.assertIn("'(-f --force)'{-f,--force}'[overwrite local edits (requires skill names)]'", self.script())


if __name__ == "__main__":
    unittest.main()
