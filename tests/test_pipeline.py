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

    def test_failure_diagnostics_are_retained(self):
        diagnostics = {'warnings': [{'code': 'access_denied', 'message': 'HTTP 403'}], 'events_scanned': 2}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(daily_scraper, 'DATA_DIR', root), patch.object(daily_scraper, 'collect_public', side_effect=CollectionError('Denied', 'access_denied', diagnostics)), patch('sys.argv', ['daily_scraper.py']):
                with self.assertRaises(SystemExit): daily_scraper.main()
            status = json.loads((root / 'collection-status.json').read_text())
            self.assertEqual(status['code'], 'access_denied')
            self.assertEqual(status['source_info'], diagnostics)
            self.assertFalse((root / 'opportunities.json').exists())

    def test_clean_empty_collection_publishes_empty_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            info = {'source': 'scoresandodds', 'availability': 'empty', 'empty_reason': 'No upcoming games.'}
            with patch.object(daily_scraper, 'DATA_DIR', root), patch.object(daily_scraper, 'collect_public', return_value=([], [], info)), patch('sys.argv', ['daily_scraper.py']):
                daily_scraper.main()
            snapshot = json.loads((root / 'opportunities.json').read_text())
            self.assertEqual(snapshot['opportunities'], [])
            self.assertEqual(json.loads((root / 'collection-status.json').read_text())['state'], 'succeeded')
