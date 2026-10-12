import json
import unittest

from helpers import FakeTerminal, TempDirTestCase, make_source_repo, read_lock, run_cli, skill_file, write_skill


class MoveCommandTest(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.library = self.root / "library"
        repo = make_source_repo(self.root / "source", {"skills/pdf/SKILL.md": skill_file("pdf")})
        run_cli("add", "acme/skills", context=FakeTerminal().context(self.library, repo))

    def move(self, name: str, namespace: str, terminal: FakeTerminal | None = None) -> tuple[int, str, str]:
        return run_cli("move", name, namespace, context=(terminal or FakeTerminal()).context(self.library))

    def statuses(self) -> dict[str, tuple[str, str]]:
        _, out, _ = run_cli("list", "-j", context=FakeTerminal().context(self.library))
        return {s["name"]: (s["namespace"], s["status"]) for s in json.loads(out)}

    def test_moves_tracked_skill_and_updates_lock(self) -> None:
        (self.library / "core").mkdir()
        code, out, _ = self.move("pdf", "core")
        self.assertEqual((code, out), (0, "Moved pdf: vendor/acme -> core\n"))
        self.assertEqual(read_lock(self.library)["skills"]["pdf"]["namespace"], "core")
        self.assertEqual(self.statuses(), {"pdf": ("core", "unchanged")})

    def test_moves_untracked_skill(self) -> None:
        write_skill(self.library, "custom", "mine")
        (self.library / "core").mkdir()
        self.assertEqual(self.move("mine", "core")[0], 0)
        self.assertEqual(self.statuses()["mine"], ("core", "untracked"))

    def test_asks_before_creating_namespace(self) -> None:
        terminal = FakeTerminal(True)
        self.move("pdf", "core", terminal)
        self.assertEqual(terminal.questions, ['Namespace "core" doesn\'t exist. Create it?'])
        self.assertEqual(self.statuses()["pdf"], ("core", "unchanged"))

    def test_declining_namespace_leaves_skill_in_place(self) -> None:
        code, out, _ = self.move("pdf", "core", FakeTerminal(False))
        self.assertEqual((code, out), (0, "Cancelled.\n"))
        self.assertEqual(self.statuses()["pdf"], ("vendor/acme", "unchanged"))
        self.assertFalse((self.library / "core").exists())

    def test_rejects_move_into_current_namespace(self) -> None:
        code, _, err = self.move("pdf", "vendor/acme")
        self.assertEqual(code, 1)
        self.assertIn("already in vendor/acme", err)

    def test_rejects_unknown_skill(self) -> None:
        code, _, err = self.move("nope", "core")
        self.assertEqual(code, 1)
        self.assertIn("no skill named 'nope'", err)

    def test_rejects_namespace_outside_library(self) -> None:
        code, _, err = self.move("pdf", "../elsewhere")
        self.assertEqual(code, 1)
        self.assertIn("invalid namespace", err)


if __name__ == "__main__":
    unittest.main()
