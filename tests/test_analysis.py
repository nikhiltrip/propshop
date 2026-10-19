import copy
from datetime import datetime, timezone
import unittest
from analysis import (
    american_to_probability,
    calculate_no_vig_probability,
    expected_return,
    threshold,
    PAYOUTS,
    compare,
    canonical_stat,
)
from collectors import parse_prizepicks, parse_fanduel

NOW = datetime(2030, 1, 1, 10, tzinfo=timezone.utc)
BASE = {
    "player": "Test Player",
    "sport": "NBA",
    "stat": "Points",
    "line": "25.5",
    "start_time": "2030-01-01T12:00:00Z",
    "observed_at": "2030-01-01T09:59:00Z",
    "period": "full_game",
}
PP = {**BASE, "variant": "standard"}
FD = {**BASE, "over_odds": "-150", "under_odds": "+120"}


class AnalysisTests(unittest.TestCase):
    def test_string_odds_and_no_vig(self):
        self.assertEqual(american_to_probability("-150"), 60)
        over, under = calculate_no_vig_probability("-150", "+120")
        self.assertAlmostEqual(over + under, 100)
        self.assertAlmostEqual(over, 56.8965517241)
        for bad in ["NaN", "inf", 0, 90, -99]:
            with self.assertRaises(ValueError):
                american_to_probability(bad)

    def test_flex_partial_payouts(self):
        self.assertAlmostEqual(expected_return([0.5] * 3, PAYOUTS["3-Pick Flex"]), 0.75)
        self.assertAlmostEqual(
            expected_return([0.5, 0.5], PAYOUTS["2-Pick Flex"]), 0.75
        )
        self.assertAlmostEqual(threshold("2-Pick Power"), 100 / 3**0.5)
        for name in PAYOUTS:
            self.assertAlmostEqual(
                expected_return([threshold(name) / 100] * int(name[0]), PAYOUTS[name]),
                1,
            )

    def test_unequal_probabilities(self):
        self.assertAlmostEqual(expected_return([0.6, 0.7], {2: 3}), 1.26)

    def test_exact_market_and_direction(self):
        rows = compare([PP], [FD], NOW)["opportunities"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["direction"], "over")
        self.assertGreater(rows[0]["edge"], 0)
        self.assertEqual(
            compare([PP], [{**FD, "over_odds": 120, "under_odds": -150}], NOW)[
                "opportunities"
            ][0]["direction"],
            "under",
        )

    def test_reject_mismatches_and_stale_data(self):
        for field, value in [
            ("stat", "Pts+Rebs"),
            ("line", 26.5),
            ("sport", "NHL"),
            ("start_time", "2030-01-02T12:00:00Z"),
            ("period", "first_half"),
            ("observed_at", "2030-01-01T09:00:00Z"),
            ("over_odds", None),
        ]:
            with self.subTest(field=field):
                self.assertEqual(
                    compare([PP], [{**FD, field: value}], NOW)["opportunities"], []
                )
        for change in [
            {"variant": "goblin"},
            {"line": 25},
            {"period": "unknown"},
            {"observed_at": "2030-01-01T11:00:00Z"},
        ]:
            self.assertEqual(
                compare([{**PP, **change}], [FD], NOW)["opportunities"], []
            )
        self.assertEqual(compare([PP], [FD, FD], NOW)["opportunities"], [])
        self.assertNotEqual(canonical_stat("points"), canonical_stat("pts+rebs"))

    def test_legacy_or_missing_metadata_rejected(self):
        self.assertEqual(
            compare([{"player": "Test Player", "line": 25.5}], [FD], NOW)[
                "opportunities"
            ],
            [],
        )

    def test_fanduel_fixture(self):
        payload = {
            "attachments": {
                "events": {"1": {"openDate": BASE["start_time"], "name": "A at B"}},
                "markets": {
                    "2": {
                        "eventId": 1,
                        "marketName": "Test Player - Points",
                        "marketStatus": "OPEN",
                        "runners": [
                            {
                                "runnerName": "Over 25.5",
                                "winRunnerOdds": {
                                    "americanDisplayOdds": {"americanOdds": "-150"}
                                },
                            },
                            {
                                "runnerName": "Under 25.5",
                                "winRunnerOdds": {
                                    "americanDisplayOdds": {"americanOdds": "+120"}
                                },
                            },
                        ],
                    }
                },
            }
        }
        rows = parse_fanduel(payload, "NBA")
        self.assertEqual(rows[0]["over_odds"], -150)
        payload["attachments"]["markets"]["2"][
            "marketName"
        ] = "Test Player - 1st Half Points"
        self.assertEqual(parse_fanduel(payload, "NBA"), [])

    def test_prizepicks_fixture(self):
        payload = {
            "included": [
                {
                    "id": "p",
                    "type": "new_player",
                    "attributes": {"display_name": "Test Player"},
                },
                {"id": "l", "type": "league", "attributes": {"name": "NBA"}},
            ],
            "data": [
                {
                    "id": "1",
                    "type": "projection",
                    "attributes": {
                        "stat_type": "Points",
                        "line_score": 25.5,
                        "start_time": BASE["start_time"],
                        "status": "pre_game",
                        "odds_type": "standard",
                    },
                    "relationships": {
                        "new_player": {"data": {"id": "p", "type": "new_player"}},
                        "league": {"data": {"id": "l", "type": "league"}},
                    },
                }
            ],
        }
        self.assertEqual(len(parse_prizepicks(payload)), 1)
        for kind in ["goblin", "demon", None]:
            modified = copy.deepcopy(payload)
            modified["data"][0]["attributes"]["odds_type"] = kind
            self.assertEqual(parse_prizepicks(modified), [])


if __name__ == "__main__":
    unittest.main()
