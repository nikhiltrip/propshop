"""Synthetic provider contracts. No live requests or private/account data."""

import copy
import json
from datetime import datetime, timezone
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from analysis import compare
from collectors import CollectionError
from public_feed import parse_schedule, parse_comparison, PageParser, PublicClient, discover_markets, PATH_MARKETS

EVENT = {
    "id": "nfl/123",
    "sport": "NFL",
    "start_time": "2030-01-01T12:00:00Z",
    "event": "A @ B",
    "home": "B",
    "away": "A",
    "url": "https://www.scoresandodds.com/nfl/b-vs-a",
}
NOW = datetime(2030, 1, 1, 10, tzinfo=timezone.utc)
OBSERVED = "2030-01-01T09:59:00Z"
PAYLOAD = {
    "event": {"sport": "nfl", "home": {"key": "B"}, "away": {"key": "A"}},
    "markets": [
        {
            "id": "nfl.123.0.55.payds",
            "stat": "passing yards",
            "available": True,
            "player": {"first_name": "Synthetic", "last_name": "Player"},
            "projection": "PREMIUM_FIELD_MUST_NOT_BE_USED",
            "date": 1893456000,
            "comparison": {
                "prizepicks": {
                    "value": 210.5,
                    "available": True,
                    "over": -137,
                    "under": -137,
                },
                "draftkings": {
                    "value": 210.5,
                    "available": True,
                    "over": -150,
                    "under": 120,
                },
                "fanduel": {
                    "value": 210.5,
                    "available": True,
                    "over": -120,
                    "under": -110,
                },
                "sleeper": {
                    "value": 210.5,
                    "available": True,
                    "over": -137,
                    "under": -137,
                },
                "betmgm": {
                    "value": 209.5,
                    "available": True,
                    "over": -120,
                    "under": -110,
                },
            },
        }
    ],
}


class PublicFeedTests(unittest.TestCase):
    def test_same_event_two_sided_prices_with_provenance(self):
        pp, books = parse_comparison(PAYLOAD, EVENT, OBSERVED)
        self.assertEqual(len(pp), 1)
        self.assertEqual(pp[0]["variant"], "provider_main")
        self.assertEqual(len(books), 3)
        self.assertNotIn("PREMIUM", json.dumps([pp, books]))
        rows = compare(pp, books, NOW)["opportunities"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(
            row["book_count"], 2
        )  # Different-line BetMGM quote is excluded.
        self.assertFalse(row["payout_verified"])
        self.assertGreater(row["no_vig_over"], 51)
        self.assertLess(row["no_vig_over"], 56.9)  # Median, not most optimistic book.

    def test_wrong_event_period_and_unavailable_pp_rejected(self):
        for edit in ["period", "team", "prizepicks"]:
            payload = copy.deepcopy(PAYLOAD)
            if edit == "period":
                payload["markets"][0]["id"] = "nfl.123.1.55.payds"
            if edit == "team":
                payload["event"]["home"]["key"] = "OTHER"
            if edit == "prizepicks":
                payload["markets"][0]["comparison"]["prizepicks"]["available"] = False
            self.assertEqual(parse_comparison(payload, EVENT, OBSERVED), ([], []))

    def test_missing_or_one_sided_quote_cannot_reach_analysis(self):
        payload = copy.deepcopy(PAYLOAD)
        del payload["markets"][0]["comparison"]["draftkings"]["under"]
        payload["markets"][0]["comparison"]["fanduel"]["under"] = 0
        pp, books = parse_comparison(payload, EVENT, OBSERVED)
        self.assertEqual(compare(pp, books, NOW)["opportunities"], [])

    def test_schedule_explicit_identity_and_timezone(self):
        event = {
            "@type": "SportsEvent",
            "eventStatus": "https://schema.org/EventScheduled",
            "identifier": 123,
            "name": "A @ B",
            "startDate": "2030-01-01T07:00:00-05:00",
            "url": EVENT["url"],
            "homeTeam": {"name": "B Home"},
            "awayTeam": {"name": "A Away"},
        }
        html = '<script type="application/ld+json">' + json.dumps(event) + "</script>"
        rows = parse_schedule(html, "NFL")
        self.assertEqual(rows[0]["id"], EVENT["id"])
        self.assertEqual(rows[0]["start_time"], "2030-01-01T12:00:00+00:00")
        event["startDate"] = "2030-01-01T12:00:00"
        self.assertEqual(
            parse_schedule(
                '<script type="application/ld+json">' + json.dumps(event) + "</script>",
                "NFL",
            ),
            [],
        )

    def test_new_categories_are_discovered_only_when_published(self):
        parser = PageParser()
        parser.feed('<a data-endpoint="/nfl/props/completions"></a>'
                    '<a data-endpoint="/nfl/props/passing-&amp;-rushing-yards"></a>'
                    '<a data-endpoint="/nfl/props/first-touchdown-scorer"></a>')
        supported, unsupported = discover_markets(parser)
        self.assertEqual(supported, ["completions", "passing & rushing yards"])
        self.assertEqual(unsupported, ["first-touchdown-scorer"])
        from analysis import canonical_stat
        for stat in PATH_MARKETS.values():
            self.assertIsNotNone(canonical_stat(stat), stat)
        self.assertNotEqual(canonical_stat("passing yards"), canonical_stat("passing & rushing yards"))
        payload = copy.deepcopy(PAYLOAD)
        payload["markets"][0]["stat"] = "completions"
        pp, books = parse_comparison(payload, EVENT, OBSERVED)
        self.assertEqual(len(compare(pp, books, NOW)["opportunities"]), 1)

    def test_access_denials_do_not_retry(self):
        with patch(
            "public_feed.urlopen",
            side_effect=HTTPError("public", 403, "Forbidden", {}, None),
        ) as request:
            client = PublicClient()
            with self.assertRaises(CollectionError):
                client.get("https://www.scoresandodds.com/nfl")
            with self.assertRaises(CollectionError):
                client.get("https://www.scoresandodds.com/nfl/props")
            self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()

class PublicBudgetTests(unittest.TestCase):
    def test_deadline_does_not_send_request(self):
        with patch('public_feed.urlopen') as request:
            client = PublicClient(timeout=0)
            with self.assertRaises(CollectionError) as error:
                client.get('https://www.scoresandodds.com/nba')
            self.assertEqual(error.exception.code, 'deadline')
            request.assert_not_called()
