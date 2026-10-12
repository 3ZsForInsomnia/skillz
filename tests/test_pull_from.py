import json
import unittest

from helpers import FakeTerminal, InstalledSourceTestCase, run_cli, write_skill


class PullFromTest(InstalledSourceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.work = self.root / "platform" / ".claude" / "skills"
        write_skill(self.work, "", "deploy", description="Ship it.")
        write_skill(self.work, "infra", "terraform")

    def pulled_cli(self, *argv: str, terminal: FakeTerminal | None = None) -> tuple[int, str, str]:
        terminal = terminal or FakeTerminal()
        namespaces = {"work": {"pull_from": str(self.work)}}
        return run_cli(*argv, context=terminal.context(self.library, self.repo, namespaces))

    def listed(self) -> dict[str, dict]:
        return {s["name"]: s for s in json.loads(self.pulled_cli("list", "-j")[1])}

    def test_pulled_skills_are_listed_as_external_under_the_namespace(self) -> None:
        skills = self.listed()
        self.assertEqual(
            (skills["deploy"]["namespace"], skills["deploy"]["status"], skills["deploy"]["description"]),
            ("work", "external", "Ship it."),
        )
        self.assertEqual(skills["deploy"]["path"], str(self.work / "deploy"))
        self.assertEqual(skills["terraform"]["namespace"], "work/infra")
        self.assertEqual(skills["pdf"]["status"], "unchanged")

    def test_missing_pull_folder_warns_and_lists_the_rest(self) -> None:
        terminal = FakeTerminal()
        context = terminal.context(self.library, namespaces={"work": {"pull_from": str(self.root / "absent")}})
        _, out, _ = run_cli("list", "-j", context=context)
        self.assertEqual({s["name"] for s in json.loads(out)}, {"pdf", "docx"})
        self.assertIn("doesn't exist", terminal.warnings[0])

    def test_add_refuses_a_pulled_namespace(self) -> None:
        for namespace in ("work", "work/infra"):
            with self.subTest(namespace=namespace):
                code, _, err = self.pulled_cli("add", "acme/skills", "pdf", "-n", namespace)
                self.assertEqual(code, 1)
                self.assertIn("skillz doesn't write there", err)

    def test_move_refuses_a_pulled_namespace(self) -> None:
        code, _, err = self.pulled_cli("move", "pdf", "work")
        self.assertEqual(code, 1)
        self.assertIn("skillz doesn't write there", err)

    def test_move_refuses_an_external_skill(self) -> None:
        (self.library / "core").mkdir()
        code, _, err = self.pulled_cli("move", "deploy", "core")
        self.assertEqual(code, 1)
        self.assertIn("deploy is external", err)
        self.assertTrue((self.work / "deploy").is_dir())

    def test_remove_refuses_an_external_skill(self) -> None:
        code, _, err = self.pulled_cli("remove", "deploy")
        self.assertEqual(code, 1)
        self.assertIn("not tracked by skillz: deploy", err)

    def test_pulled_names_count_toward_uniqueness(self) -> None:
        write_skill(self.work, "", "pdf")
        code, _, err = self.pulled_cli("move", "docx", "custom")
        self.assertEqual(code, 1)
        self.assertIn("'pdf' exists in more than one namespace", err)


if __name__ == "__main__":
    unittest.main()
