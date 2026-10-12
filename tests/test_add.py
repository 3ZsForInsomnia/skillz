import json
import unittest

from helpers import (
    FakeTerminal,
    TempDirTestCase,
    commit_all,
    git,
    make_source_repo,
    read_lock,
    run_cli,
    skill_file,
    write_skill,
)


class AddCommandTest(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.library = self.root / "library"
        self.repo = make_source_repo(
            self.root / "source",
            {
                "skills/pdf/SKILL.md": skill_file("pdf"),
                "skills/pdf/refs/forms.md": "forms",
                "skills/docx/SKILL.md": skill_file("docx"),
            },
        )

    def add(self, *argv: str, terminal: FakeTerminal | None = None) -> tuple[int, str, str]:
        terminal = terminal or FakeTerminal()
        return run_cli("add", *argv, context=terminal.context(self.library, self.repo))

    def list_statuses(self) -> dict[str, tuple[str, str]]:
        _, out, _ = run_cli("list", "-j", context=FakeTerminal().context(self.library))
        return {s["name"]: (s["namespace"], s["status"]) for s in json.loads(out)}

    def test_installs_every_skill_into_vendor_owner_without_asking(self) -> None:
        code, out, err = self.add("acme/skills")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "Added to vendor/acme: docx, pdf\n")
        self.assertEqual((self.library / "vendor/acme/pdf/refs/forms.md").read_text(), "forms")
        self.assertEqual(
            self.list_statuses(), {"docx": ("vendor/acme", "unchanged"), "pdf": ("vendor/acme", "unchanged")}
        )

    def test_installs_only_named_skills(self) -> None:
        self.add("acme/skills", "pdf")
        self.assertEqual(set(self.list_statuses()), {"pdf"})
        self.assertFalse((self.library / "vendor/acme/docx").exists())

    def test_records_source_and_upstream_details_in_lock(self) -> None:
        self.add("acme/skills", "pdf")
        lock = read_lock(self.library)
        self.assertEqual(lock["sources"], {"acme/skills": {"ref": None, "skills": ["pdf"]}})
        entry = lock["skills"]["pdf"]
        self.assertEqual(
            (entry["namespace"], entry["source"], entry["path"]), ("vendor/acme", "acme/skills", "skills/pdf")
        )
        self.assertEqual(entry["commit"], git(self.repo, "rev-parse", "HEAD").strip())
        self.assertEqual(entry["upstream_hash"], git(self.repo, "rev-parse", "HEAD:skills/pdf").strip())

    def test_adding_more_from_the_same_source_extends_its_list(self) -> None:
        self.add("acme/skills", "pdf")
        self.add("acme/skills", "docx")
        self.assertEqual(read_lock(self.library)["sources"]["acme/skills"]["skills"], ["docx", "pdf"])

    def test_folder_url_installs_that_skill_with_pinned_ref(self) -> None:
        code, out, _ = self.add("https://github.com/acme/skills/tree/main/skills/docx")
        self.assertEqual((code, out), (0, "Added to vendor/acme: docx\n"))
        self.assertEqual(read_lock(self.library)["sources"], {"acme/skills@main": {"ref": "main", "skills": ["docx"]}})

    def test_new_custom_namespace_asks_first(self) -> None:
        terminal = FakeTerminal(True)
        self.add("acme/skills", "pdf", "-n", "core", terminal=terminal)
        self.assertEqual(terminal.questions, ['Namespace "core" doesn\'t exist. Create it?'])
        self.assertEqual(self.list_statuses(), {"pdf": ("core", "unchanged")})

    def test_declining_new_namespace_changes_nothing(self) -> None:
        code, out, _ = self.add("acme/skills", "pdf", "-n", "core", terminal=FakeTerminal(False))
        self.assertEqual((code, out), (0, "Cancelled.\n"))
        self.assertFalse(self.library.exists() and any(self.library.iterdir()))

    def test_existing_custom_namespace_does_not_ask(self) -> None:
        (self.library / "core").mkdir(parents=True)
        self.assertEqual(self.add("acme/skills", "pdf", "-n", "core")[0], 0)

    def test_rejects_a_name_already_in_the_library(self) -> None:
        write_skill(self.library, "custom", "pdf")
        code, _, err = self.add("acme/skills")
        self.assertEqual(code, 1)
        self.assertIn("already in the library: pdf", err)
        self.assertFalse((self.library / "vendor").exists())

    def test_rejects_unknown_skill_names(self) -> None:
        code, _, err = self.add("acme/skills", "pdf", "nope")
        self.assertEqual(code, 1)
        self.assertIn("not found in acme/skills: nope", err)

    def test_rejects_names_alongside_folder_url(self) -> None:
        code, _, err = self.add("https://github.com/acme/skills/tree/main/skills/docx", "pdf")
        self.assertEqual(code, 1)
        self.assertIn("don't also pass skill names", err)

    def test_identical_copies_install_the_one_highest_in_the_repo(self) -> None:
        build_copy = self.repo / "dist/plugins/pdf/skills/pdf"
        build_copy.mkdir(parents=True)
        for file in ("SKILL.md", "refs/forms.md"):
            (build_copy / file).parent.mkdir(parents=True, exist_ok=True)
            (build_copy / file).write_text((self.repo / "skills/pdf" / file).read_text())
        commit_all(self.repo)
        code, _, err = self.add("acme/skills", "pdf")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(read_lock(self.library)["skills"]["pdf"]["path"], "skills/pdf")

    def test_differing_copies_are_an_error_suggesting_the_folder_url(self) -> None:
        (self.repo / "dist/pdf").mkdir(parents=True)
        (self.repo / "dist/pdf/SKILL.md").write_text(skill_file("pdf") + "different\n")
        commit_all(self.repo)
        code, _, err = self.add("acme/skills", "pdf")
        self.assertEqual(code, 1)
        self.assertIn("differing copies in the repo (dist/pdf, skills/pdf)", err)
        self.assertIn("folder URL", err)

    def test_reports_git_failures_as_errors(self) -> None:
        terminal = FakeTerminal()
        code, _, err = run_cli("add", "acme/skills", context=terminal.context(self.library, self.root / "absent"))
        self.assertEqual(code, 1)
        self.assertIn("git clone", err)


if __name__ == "__main__":
    unittest.main()
