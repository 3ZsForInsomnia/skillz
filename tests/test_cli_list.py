import json
import os
import unittest
from unittest import mock

from helpers import TempDirTestCase, lock_entry, run_cli, write_lock, write_skill


class ListCommandTest(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.library = self.root / "library"
        config = self.root / "config" / "skillz"
        config.mkdir(parents=True)
        (config / "skillz.toml").write_text(f'library = "{self.library}"\n')
        patcher = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.root / "config")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        return run_cli(*argv)

    def test_empty_library_says_so(self) -> None:
        self.assertEqual(self.run_cli("list"), (0, "No skills found.\n", ""))

    def test_table_lists_every_skill_with_status(self) -> None:
        write_skill(self.library, "custom", "lbm", description="Offload text.")
        write_lock(self.library, {"pdf": lock_entry("vendor/acme")})
        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines(),
            [
                "NAMESPACE    NAME  STATUS     DESCRIPTION",
                "custom       lbm   untracked  Offload text.",
                "vendor/acme  pdf   missing",
            ],
        )

    def test_long_descriptions_are_truncated(self) -> None:
        write_skill(self.library, "custom", "lbm", description="x" * 80)
        _, out, _ = self.run_cli("list")
        self.assertTrue(out.splitlines()[1].endswith("x" * 59 + "…"))

    def test_json_output_lists_every_field(self) -> None:
        folder = write_skill(self.library, "custom", "lbm", description="Offload text.")
        _, out, _ = self.run_cli("list", "-j")
        self.assertEqual(
            json.loads(out),
            [
                {
                    "name": "lbm",
                    "namespace": "custom",
                    "status": "untracked",
                    "description": "Offload text.",
                    "path": str(folder),
                    "source": None,
                }
            ],
        )

    def test_bad_lock_prints_error_and_fails(self) -> None:
        self.library.mkdir()
        (self.library / "skillz.lock.json").write_text("{nope")
        code, out, err = self.run_cli("list")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("skillz: ", err)
        self.assertIn("skillz.lock.json", err)


if __name__ == "__main__":
    unittest.main()
