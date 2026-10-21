import copy
import json
from pathlib import Path
import tempfile
import unittest
from analysis import compare
from history import record_snapshot, connect, export_history
from results import grade, identify_event, player_stat
from test_analysis import PP, FD, NOW


def payload(name='Test Player', stats=None, final=True):
    return {'header': {'id': '123', 'competitions': [{'status': {'type': {'completed': final, 'name': 'STATUS_FINAL' if final else 'STATUS_IN_PROGRESS'}}}]},
            'boxscore': {'players': [{'statistics': [{'name': 'passing', 'labels': ['C/ATT', 'YDS', 'INT'],
                'athletes': [{'athlete': {'id': '1', 'displayName': name}, 'stats': stats or ['20/30', '250', '0']}]}]}]}}


class HistoryTests(unittest.TestCase):
    def test_frozen_first_positive_observation_and_backfill_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = compare([PP], [FD], NOW)
            snapshot['last_updated'] = NOW.isoformat()
            record_snapshot(folder, snapshot)
            row = snapshot['opportunities'][0]
            probability = row['no_vig_win_pct']
            row['no_vig_win_pct'] = 99
            record_snapshot(folder, snapshot)
            self.assertEqual(export_history(folder)['records'][0]['probability'], probability)
            with connect(folder) as db: self.assertEqual(db.execute('SELECT count(*) FROM snapshots').fetchone()[0], 1)
            other = copy.deepcopy(snapshot)
            other['opportunities'][0]['id'] = 'reconstructed'
            record_snapshot(folder, other, backfilled=True)
            self.assertEqual(export_history(folder)['backfilled_count'], 1)

    def test_negative_and_post_start_observations_do_not_enter_positive_history(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = compare([PP], [FD], NOW)
            snapshot['last_updated'] = '2030-01-01T13:00:00Z'
            record_snapshot(folder, snapshot)
            self.assertEqual(export_history(folder)['records'], [])

    def test_final_zero_interceptions_is_a_hypothetical_win_not_a_settlement(self):
        row = {'player': 'Test Player', 'sport': 'NFL', 'stat': 'interceptions', 'line': 0.5, 'direction': 'under'}
        outcome, actual, reason = grade(payload(), row)
        self.assertEqual((outcome, actual), ('hypothetical_win', 0))
        self.assertIn('unverified', reason)
        self.assertEqual(grade(payload(final=False), row)[0], 'pending')

    def test_missing_player_and_zero_participation_are_not_assumed_zero(self):
        row = {'player': 'Missing', 'sport': 'NFL', 'stat': 'interceptions', 'line': 0.5, 'direction': 'under'}
        self.assertEqual(grade(payload(), row)[0], 'unresolved')
        row['player'] = 'Test Player'
        self.assertEqual(grade(payload(stats=['0/0', '0', '0']), row)[0], 'unresolved')

    def test_event_matching_requires_teams_and_time(self):
        row = {'sport': 'NFL', 'home_team': 'SF', 'away_team': 'WAS', 'start_time': '2030-01-01T12:00:00Z'}
        event = {'id': '1', 'date': row['start_time'], 'competitions': [{'competitors': [{'homeAway': 'home', 'team': {'abbreviation': 'SF'}}, {'homeAway': 'away', 'team': {'abbreviation': 'WSH'}}]}]}
        self.assertEqual(identify_event(row, [event]), '1')
        self.assertIsNone(identify_event(row, [event, event]))
        event['date'] = '2030-01-02T12:00:00Z'
        self.assertIsNone(identify_event(row, [event]))

    def test_baseball_innings_are_outs_not_decimal_innings(self):
        p = {'boxscore': {'players': [{'statistics': [{'labels': ['IP'], 'athletes': [{'athlete': {'id': '1', 'displayName': 'Pitcher'}, 'stats': ['5.2']}]}]}]}}
        self.assertEqual(player_stat(p, {'player': 'Pitcher', 'sport': 'MLB', 'stat': 'outs'}), 17)
