import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import daily_scraper
from collectors import CollectionError


class PipelineTests(unittest.TestCase):
    def test_collection_failure_preserves_snapshot_and_records_failure(self):
        async def fail(*args):
            raise CollectionError("Access restricted; stopped.")

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = {
                "schema_version": 2,
                "last_updated": "2030-01-01T00:00:00Z",
                "opportunities": [],
            }
            daily_scraper.atomic_json(root / "opportunities.json", old)
            with patch.object(daily_scraper, "DATA_DIR", root), patch.object(
                daily_scraper, "collect_browser", fail
            ), patch("sys.argv", ["daily_scraper.py", "--source", "browser"]):
                with self.assertRaises(SystemExit) as result:
                    daily_scraper.main()
                self.assertEqual(result.exception.code, 1)
            self.assertEqual(json.loads((root / "opportunities.json").read_text()), old)
            self.assertEqual(
                json.loads((root / "collection-status.json").read_text())["state"],
                "failed",
            )
            self.assertEqual(list(root.glob("*.tmp")), [])

    def test_atomic_file_rejects_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "snapshot.json"
            daily_scraper.atomic_json(file, {"ok": True})
            with self.assertRaises(ValueError):
                daily_scraper.atomic_json(file, {"bad": float("nan")})
            self.assertEqual(json.loads(file.read_text()), {"ok": True})
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])
