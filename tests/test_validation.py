from datetime import datetime, timezone
import unittest
from analysis import compare
from test_analysis import PP, FD, NOW
from validate_snapshot import audit


class ValidationTests(unittest.TestCase):
    def snapshot(self):
        data = compare([PP], [FD], NOW)
        data["last_updated"] = NOW.isoformat()
        return data

    def test_independent_price_audit_catches_corrupt_consensus(self):
        data = self.snapshot()
        self.assertTrue(audit(data, now=NOW)["integrity_passed"])
        data["opportunities"][0]["no_vig_over"] = 60
        data["opportunities"][0]["no_vig_under"] = 40
        result = audit(data, now=NOW)
        self.assertFalse(result["integrity_passed"])
        self.assertIn("median", result["errors"][0]["problem"])

    def test_line_check_distinguishes_mismatch_missing_and_unverified(self):
        check = {**PP, "line": 24.5, "board_refreshed": True}
        result = audit(self.snapshot(), [check], now=NOW)
        self.assertEqual(result["manual_checks"][0]["status"], "mismatched")
        self.assertTrue(result["integrity_passed"])  # Correct math does not prove correct source lines.
        check["board_refreshed"] = False
        self.assertEqual(audit(self.snapshot(), [check], now=NOW)["manual_checks"][0]["status"], "unverified")
        check["player"] = "Missing Player"
        self.assertEqual(audit(self.snapshot(), [check], now=NOW)["manual_checks"][0]["status"], "not_comparable")

    def test_old_feed_record_is_distinct_from_retrieval_freshness(self):
        data = self.snapshot()
        data["opportunities"][0]["provider_updated_at"] = "2030-01-01T09:00:00Z"
        report = audit(data, now=NOW)
        self.assertTrue(report["integrity_passed"])
        self.assertEqual(report["feed_records_older_than_15m"], 1)
        self.assertIn("record-level", report["warnings"][0])

    def test_reaudit_of_old_snapshot_warns_and_preserves_collection_day(self):
        report = audit(self.snapshot(), now=datetime(2030, 1, 3, tzinfo=timezone.utc))
        self.assertTrue(report["warnings"])
        self.assertEqual(report["collection_day_pacific"], "2030-01-01")
