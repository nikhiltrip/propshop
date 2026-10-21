"""Immutable local observations, plus separately stored hypothetical outcomes."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import os

from analysis import parse_time, utc_now


def connect(data_dir):
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(Path(data_dir) / 'history.sqlite', timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS snapshots (collected_at TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    db.execute('''CREATE TABLE IF NOT EXISTS predictions (
        key TEXT PRIMARY KEY, first_seen TEXT NOT NULL, row TEXT NOT NULL,
        backfilled INTEGER NOT NULL, outcome TEXT NOT NULL DEFAULT 'pending',
        actual REAL, checked_at TEXT, reason TEXT, source_url TEXT)''')
    return db


def record_snapshot(data_dir, snapshot, backfilled=False):
    stamp = snapshot['last_updated']
    with connect(data_dir) as db:
        db.execute('INSERT OR IGNORE INTO snapshots VALUES (?,?)', (stamp, json.dumps(snapshot, allow_nan=False)))
        for row in snapshot['opportunities']:
            if row.get('edge', 0) <= 0 or parse_time(stamp) >= parse_time(row['start_time']):
                continue
            key = hashlib.sha256((row['id'] + ':' + row['direction']).encode()).hexdigest()[:24]
            db.execute('''INSERT OR IGNORE INTO predictions (key,first_seen,row,backfilled) VALUES (?,?,?,?)''',
                       (key, stamp, json.dumps(row, allow_nan=False), int(backfilled)))
    export_history(data_dir)


def export_history(data_dir):
    with connect(data_dir) as db:
        entries = db.execute('SELECT key,first_seen,row,backfilled,outcome,actual,checked_at,reason,source_url FROM predictions ORDER BY first_seen DESC,key').fetchall()
    records = []
    for key, first, raw, backfilled, outcome, actual, checked, reason, url in entries:
        row = json.loads(raw)
        if row.get('edge', 0) <= 0:
            continue
        records.append({'key': key, 'first_seen': first, 'player': row['player'], 'sport': row['sport'],
                        'stat': row['stat'], 'line': row['line'], 'direction': row['direction'],
                        'probability': row['no_vig_win_pct'], 'edge': row['edge'], 'start_time': row['start_time'],
                        'backfilled': bool(backfilled), 'outcome': outcome, 'actual': actual,
                        'checked_at': checked, 'reason': reason, 'source_url': url})
    counts = {name: sum(r['outcome'] == name and not r['backfilled'] for r in records)
              for name in ['hypothetical_win', 'hypothetical_loss', 'pending', 'unresolved', 'tie']}
    payload = {'updated_at': utc_now(), 'tracked_positive_estimates': len(records), 'counts': counts,
               'records': records[:200], 'backfilled_count': sum(r['backfilled'] for r in records),
               'methodology': 'First observed positive model estimates at each line/direction. Hypothetical outcomes against the saved feed line, not verified PrizePicks settlement, actual bets, or profit. Backfilled rows are excluded from prospective counts. Related props are not independent.'}
    path = Path(data_dir) / 'results.json'
    fd, name = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(payload, stream, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return payload
