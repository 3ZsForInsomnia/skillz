import os
import unittest
from pathlib import Path
from unittest import mock

from helpers import TempDirTestCase

from skillz.manifest import ManifestError, load_manifest


class LoadManifestTest(TempDirTestCase):
    def write_manifest(self, text: str) -> Path:
        path = self.root / "skillz.toml"
        path.write_text(text)
        return path

    def test_missing_file_uses_xdg_config_dir_as_library(self) -> None:
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.root / "config")}):
            manifest = load_manifest(self.root / "absent.toml")
        self.assertEqual(manifest.library, self.root / "config" / "skillz")
        self.assertEqual(dict(manifest.namespaces), {})

    def test_reads_library_and_namespace_settings(self) -> None:
        path = self.write_manifest(
            f'library = "{self.root}/lib"\n'
            "[namespaces.core]\n"
            f'link_to = "{self.root}/claude"\n'
            '[namespaces."team/work"]\n'
            f'pull_from = "{self.root}/work"\n'
        )
        manifest = load_manifest(path)
        self.assertEqual(manifest.library, self.root / "lib")
        self.assertEqual(manifest.namespaces["core"].link_to, self.root / "claude")
        self.assertIsNone(manifest.namespaces["core"].pull_from)
        self.assertEqual(manifest.namespaces["team/work"].pull_from, self.root / "work")

    def test_expands_home_in_paths(self) -> None:
        path = self.write_manifest('library = "~/lib"\n')
        self.assertEqual(load_manifest(path).library, Path.home() / "lib")

    def test_rejects_unknown_top_level_key(self) -> None:
        path = self.write_manifest('librery = "/tmp/x"\n')
        with self.assertRaisesRegex(ManifestError, "librery"):
            load_manifest(path)

    def test_rejects_unknown_namespace_key(self) -> None:
        path = self.write_manifest('[namespaces.core]\nlink = "/tmp/x"\n')
        with self.assertRaisesRegex(ManifestError, "namespaces.core.*link"):
            load_manifest(path)

    def test_rejects_link_to_and_pull_from_together(self) -> None:
        path = self.write_manifest('[namespaces.core]\nlink_to = "/a"\npull_from = "/b"\n')
        with self.assertRaisesRegex(ManifestError, "cannot both be set"):
            load_manifest(path)

    def test_rejects_namespace_escaping_the_library(self) -> None:
        path = self.write_manifest('[namespaces."../outside"]\nlink_to = "/a"\n')
        with self.assertRaisesRegex(ManifestError, "relative folder path"):
            load_manifest(path)

    def test_rejects_empty_path(self) -> None:
        path = self.write_manifest('library = ""\n')
        with self.assertRaisesRegex(ManifestError, "^library: expected"):
            load_manifest(path)

    def test_reports_invalid_toml_with_file_path(self) -> None:
        path = self.write_manifest("library = \n")
        with self.assertRaisesRegex(ManifestError, "skillz.toml"):
            load_manifest(path)


if __name__ == "__main__":
    unittest.main()
