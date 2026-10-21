#!/usr/bin/env python3
"""Update hypothetical outcomes from public ESPN box scores; never place bets."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from analysis import canonical_stat, normalize, parse_time, utc_now
from history import connect, export_history

PATHS = {'NFL': 'football/nfl', 'NBA': 'basketball/nba', 'NHL': 'hockey/nhl', 'MLB': 'baseball/mlb'}
ALIASES = {'NBA': {'SAS': 'SA', 'NYK': 'NY', 'GSW': 'GS', 'NOP': 'NO', 'UTA': 'UTAH'},
           'NFL': {'WAS': 'WSH'}, 'NHL': {'UTAH': 'UTA', 'LAK': 'LA', 'NJD': 'NJ', 'TBL': 'TB', 'SJS': 'SJ'},
           'MLB': {'WSN': 'WSH', 'SDP': 'SD', 'SFG': 'SF', 'TBR': 'TB', 'KCR': 'KC'}}


def code(sport, value):
    return ALIASES.get(sport, {}).get(value, value)


def identify_event(row, events):
    matches = []
    for event in events:
        if abs((parse_time(event['date']) - parse_time(row['start_time'])).total_seconds()) > 900:
            continue
        teams = {t['homeAway']: t['team']['abbreviation'] for t in event['competitions'][0]['competitors']}
        if row.get('home_team') and row.get('away_team') and all(
            code(row['sport'], row[k + '_team']) == code(row['sport'], teams[k]) for k in ['home', 'away']):
            matches.append(event['id'])
    return matches[0] if len(matches) == 1 else None


def numeric(value):
    result = float(value)
    if not __import__('math').isfinite(result):
        raise ValueError('Nonfinite stat')
    return result


def player_stat(payload, row):
    """Require an explicit applicable box-score row; absence is never assumed zero."""
    candidates = []
    stat, sport = canonical_stat(row['stat']), row['sport']
    for team in payload.get('boxscore', {}).get('players', []):
        for group in team.get('statistics', []):
            for athlete in group.get('athletes', []):
                if normalize(athlete.get('athlete', {}).get('displayName')) != normalize(row['player']):
                    continue
                if athlete.get('didNotPlay') or athlete.get('notActive'): continue
                labels = group.get('labels', [])
                values = dict(zip(labels, athlete.get('stats', [])))
                name = group.get('name')
                try:
                    value = None
                    if sport == 'NFL':
                        if name == 'passing' and numeric(values['C/ATT'].split('/')[1]) <= 0: continue
                        if name == 'rushing' and numeric(values.get('CAR', 0)) <= 0: continue
                        if name == 'receiving' and numeric(values.get('TGTS', 0)) + numeric(values.get('REC', 0)) <= 0: continue
                        if name == 'kicking' and sum(numeric(values.get(k, '0/0').split('/')[-1]) for k in ['FG', 'XP']) <= 0: continue
                        mapping = {'passing_yards': ('passing', 'YDS'), 'passing_tds': ('passing', 'TD'),
                                   'interceptions': ('passing', 'INT'), 'rushing_yards': ('rushing', 'YDS'),
                                   'rush_attempts': ('rushing', 'CAR'), 'longest_rush': ('rushing', 'LONG'),
                                   'receiving_yards': ('receiving', 'YDS'), 'receptions': ('receiving', 'REC'),
                                   'longest_reception': ('receiving', 'LONG'), 'kicking_points': ('kicking', 'PTS')}
                        if stat in mapping and name == mapping[stat][0]:
                            value = numeric(values[mapping[stat][1]])
                        if stat in ('completions', 'pass_attempts') and name == 'passing':
                            value = numeric(values['C/ATT'].split('/')[stat == 'pass_attempts'])
                    elif sport == 'NBA':
                        if not values.get('MIN') or values['MIN'] in ('0', '0:00', '--'): continue
                        mapping = {'points': ['PTS'], 'rebounds': ['REB'], 'assists': ['AST'], 'steals': ['STL'],
                                   'points_rebounds_assists': ['PTS', 'REB', 'AST'], 'points_rebounds': ['PTS', 'REB'],
                                   'points_assists': ['PTS', 'AST'], 'rebounds_assists': ['REB', 'AST']}
                        if stat in mapping:
                            value = sum(numeric(values[k]) for k in mapping[stat])
                        if stat == 'threes': value = numeric(values['3PT'].split('-')[0])
                    elif sport == 'NHL':
                        if not values.get('TOI') or values['TOI'] in ('0', '0:00', '--'): continue
                        mapping = {'goals': ['G'], 'assists': ['A'], 'points': ['G', 'A'],
                                   'shots_on_goal': ['SOG'], 'blocked_shots': ['BS'], 'saves': ['SV']}
                        if stat in mapping: value = sum(numeric(values[k]) for k in mapping[stat])
                    elif sport == 'MLB':
                        pitching = 'IP' in values
                        mapping = ({'strikeouts': 'K', 'hits_allowed': 'H', 'earned_runs_allowed': 'ER', 'walks_allowed': 'BB'} if pitching
                                   else {'hits': 'H', 'home_runs': 'HR', 'runs_batted_in': 'RBI'})
                        if stat in mapping: value = numeric(values[mapping[stat]])
                        if stat == 'hits_runs_rbis' and not pitching: value = sum(numeric(values[k]) for k in ['H', 'R', 'RBI'])
                        if stat == 'outs' and pitching:
                            innings, _, outs = values['IP'].partition('.')
                            if outs not in ('', '0', '1', '2'): raise ValueError('Invalid baseball innings')
                            value = int(innings) * 3 + int(outs or 0)
                    if value is not None:
                        candidates.append((athlete['athlete'].get('id', normalize(row['player'])), value))
                except (KeyError, ValueError, TypeError, IndexError):
                    continue
    unique = set(candidates)
    return unique.pop()[1] if len(unique) == 1 else None


def grade(payload, row):
    competition = payload.get('header', {}).get('competitions', [{}])[0]
    status = competition.get('status', {}).get('type', {})
    actual = player_stat(payload, row)
    if status.get('completed') is not True or status.get('name') != 'STATUS_FINAL':
        return 'pending', actual, 'Game is not confirmed final; no win/loss recorded.'
    if actual is None:
        return 'unresolved', None, 'No explicit applicable stat or ambiguous athlete. Missing is not zero; DNP/settlement needs review.'
    if actual == row['line']:
        return 'tie', actual, 'Saved line tied; PrizePicks settlement is not modeled.'
    win = actual > row['line'] if row['direction'] == 'over' else actual < row['line']
    return ('hypothetical_win' if win else 'hypothetical_loss'), actual, 'Against saved feed line only; actual PrizePicks line, payout and settlement remain unverified.'


class StatsClient:
    def __init__(self): self.deadline = time.monotonic() + 90
    def get(self, sport, endpoint, params):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0: raise RuntimeError('Result update reached its time limit; no further requests sent.')
        url = 'https://site.api.espn.com/apis/site/v2/sports/' + PATHS[sport] + '/' + endpoint + '?' + urlencode(params)
        with urlopen(Request(url, headers={'User-Agent': 'PropShop/2.0 (personal result verification)'}), timeout=min(10, remaining)) as response:
            return json.loads(response.read(8 * 1024 * 1024))


def refresh(data_dir, client=None, recheck_final=False):
    client = client or StatsClient()
    now = datetime.now(timezone.utc)
    with connect(data_dir) as db:
        where = "" if recheck_final else "WHERE outcome IN ('pending','unresolved')"
        records = db.execute(f"SELECT key,row FROM predictions {where} ORDER BY first_seen LIMIT 1000").fetchall()
    updates, schedules, summaries = [], {}, {}
    for key, raw in records:
        row = json.loads(raw)
        if parse_time(row['start_time']) > now or row['sport'] not in PATHS: continue
        date = parse_time(row['start_time']).astimezone(ZoneInfo('America/New_York')).strftime('%Y%m%d')
        schedule_key = (row['sport'], date)
        if schedule_key not in schedules: schedules[schedule_key] = client.get(row['sport'], 'scoreboard', {'dates': date})
        event_id = identify_event(row, schedules[schedule_key].get('events', []))
        if not event_id:
            updates.append(('unresolved', None, utc_now(), 'No unique time-and-team event match; no guessed result.', None, key))
            continue
        summary_key = (row['sport'], event_id)
        if summary_key not in summaries:
            if len(summaries) >= 20: break
            summaries[summary_key] = client.get(row['sport'], 'summary', {'event': event_id})
        payload = summaries[summary_key]
        if str(payload.get('header', {}).get('id')) != event_id:
            raise RuntimeError('Result provider returned the wrong event; no updates committed.')
        outcome, actual, reason = grade(payload, row)
        updates.append((outcome, actual, utc_now(), reason,
                        f'https://www.espn.com/{PATHS[row["sport"]].split("/")[-1]}/boxscore/_/gameId/{event_id}', key))
    with connect(data_dir) as db:
        db.executemany('UPDATE predictions SET outcome=?,actual=?,checked_at=?,reason=?,source_url=? WHERE key=?', updates)
    return export_history(data_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['refresh'])
    parser.add_argument('--recheck-final', action='store_true', help='Revisit completed hypothetical outcomes for source corrections')
    args = parser.parse_args()
    data_dir = Path(os.environ.get('PROPSHOP_DATA_DIR', Path(__file__).resolve().parent / 'data'))
    data_dir.mkdir(parents=True, exist_ok=True)
    from daily_scraper import atomic_json
    status = {'state': 'running', 'started_at': utc_now()}
    try:
        with open(data_dir / '.scrape.lock', 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            atomic_json(data_dir / 'results-status.json', status)
            result = refresh(data_dir, recheck_final=args.recheck_final)
        status.update(state='succeeded', finished_at=utc_now(), message='Final-stat check complete. Missing/unsupported stats remain unresolved.')
        atomic_json(data_dir / 'results-status.json', status)
        print(json.dumps(result['counts']))
    except Exception as exc:
        message = ('Public results provider denied access or rate-limited; no retry.' if isinstance(exc, HTTPError) and exc.code in (401,403,429)
                   else 'Collection is running; retry results later.' if isinstance(exc, BlockingIOError)
                   else f'Result update failed ({type(exc).__name__}); existing outcomes retained.')
        status.update(state='failed', finished_at=utc_now(), message=message)
        atomic_json(data_dir / 'results-status.json', status)
        print(message)
        raise SystemExit(1)


if __name__ == '__main__': main()
