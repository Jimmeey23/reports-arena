"""Verify that published bundled reports refresh their stable run IDs safely."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.bundles import sync_bundled_runs


class BundledRunSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.bundle = root / "bundle"
        self.storage = root / "persistent-runs"
        self.bundle.mkdir()
        self.storage.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def write_run(root, run_id, revision, report_text):
        run = root / run_id
        run.mkdir(parents=True, exist_ok=True)
        manifest = {"label": "September 2026", "studio": "Supreme HQ, Bandra"}
        if revision is not None:
            manifest["bundle_revision"] = revision
        (run / "manifest.json").write_text(json.dumps(manifest))
        (run / "report.html").write_text(report_text)
        return run

    def test_newer_bundle_updates_existing_report_without_a_new_run_id(self):
        run_id = "bandra-september"
        self.write_run(self.bundle, run_id, 1, "new report v1")
        existing = self.write_run(self.storage, run_id, None, "old report")
        (existing / "user-extra.txt").write_text("leave this alone")

        self.assertEqual(sync_bundled_runs(self.bundle, self.storage), [run_id])
        self.assertEqual((existing / "report.html").read_text(), "new report v1")
        self.assertEqual((existing / "user-extra.txt").read_text(), "leave this alone")
        self.assertEqual(json.loads((existing / "manifest.json").read_text())["bundle_revision"], 1)

        # A second startup at the same revision must not overwrite later local changes.
        (existing / "report.html").write_text("same-revision local change")
        self.assertEqual(sync_bundled_runs(self.bundle, self.storage), [])
        self.assertEqual((existing / "report.html").read_text(), "same-revision local change")

        # A deliberate next release advances the same run rather than adding a card.
        self.write_run(self.bundle, run_id, 2, "new report v2")
        self.assertEqual(sync_bundled_runs(self.bundle, self.storage), [run_id])
        self.assertEqual((existing / "report.html").read_text(), "new report v2")

    def test_missing_runs_are_seeded_but_deleted_runs_stay_deleted(self):
        self.write_run(self.bundle, "fresh", 1, "fresh report")
        self.write_run(self.bundle, "deleted", 1, "do not restore")

        self.assertEqual(sync_bundled_runs(self.bundle, self.storage, {"deleted"}), ["fresh"])
        self.assertEqual((self.storage / "fresh" / "report.html").read_text(), "fresh report")
        self.assertFalse((self.storage / "deleted").exists())

    def test_same_directory_is_not_copied_over_itself(self):
        run_id = "local"
        run = self.write_run(self.bundle, run_id, 1, "keep")
        self.assertEqual(sync_bundled_runs(self.bundle, self.bundle), [])
        self.assertEqual((run / "report.html").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
