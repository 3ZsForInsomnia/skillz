import json
import unittest

from helpers import TempDirTestCase, lock_entry, write_lock

from skillz.lock import LockError, load_lock, save_lock


class LockFileTest(TempDirTestCase):
    def test_missing_lock_is_empty(self) -> None:
        lock = load_lock(self.root)
        self.assertEqual(dict(lock.skills), {})
        self.assertEqual(dict(lock.sources), {})

    def test_reads_sources_and_skills(self) -> None:
        write_lock(
            self.root,
            skills={"pdf": lock_entry("vendor/acme")},
            sources={"acme/skills": {"ref": None, "skills": ["pdf"]}},
        )
        lock = load_lock(self.root)
        self.assertEqual(lock.skills["pdf"].namespace, "vendor/acme")
        self.assertEqual(lock.sources["acme/skills"].skills, ("pdf",))
        self.assertIsNone(lock.sources["acme/skills"].ref)

    def test_save_then_load_round_trips_the_file(self) -> None:
        write_lock(
            self.root,
            skills={"pdf": lock_entry("vendor/acme")},
            sources={"acme/skills": {"ref": "v1", "skills": ["pdf"]}},
        )
        original = json.loads((self.root / "skillz.lock.json").read_text())
        save_lock(self.root, load_lock(self.root))
        self.assertEqual(json.loads((self.root / "skillz.lock.json").read_text()), original)

    def test_save_leaves_no_temp_files(self) -> None:
        save_lock(self.root, load_lock(self.root))
        self.assertEqual([p.name for p in self.root.iterdir()], ["skillz.lock.json"])

    def test_rejects_unknown_version(self) -> None:
        (self.root / "skillz.lock.json").write_text('{"version": 99}')
        with self.assertRaisesRegex(LockError, "unsupported lock version 99"):
            load_lock(self.root)

    def test_rejects_skill_entry_missing_fields(self) -> None:
        write_lock(self.root, skills={"pdf": {"namespace": "core"}})
        with self.assertRaisesRegex(LockError, "skills.pdf"):
            load_lock(self.root)

    def test_rejects_invalid_json(self) -> None:
        (self.root / "skillz.lock.json").write_text("{nope")
        with self.assertRaisesRegex(LockError, "skillz.lock.json"):
            load_lock(self.root)


if __name__ == "__main__":
    unittest.main()
