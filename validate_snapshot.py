#!/usr/bin/env python3
"""Audit a local snapshot without making requests or changing dashboard data."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("PROPSHOP_DATA_DIR", ROOT / "data"))


def timestamp(value):
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Missing timezone")
    return dt.astimezone(timezone.utc)


def implied(price):
    price = float(price)
    if not math.isfinite(price) or abs(price) < 100:
        raise ValueError("Invalid American price")
    return 100 / (price + 100) if price > 0 else -price / (-price + 100)


def audit(snapshot, checks=(), now=None):
    now = now or datetime.now(timezone.utc)
    errors, warnings, manual = [], [], []
    if snapshot.get("schema_version") != 2 or not isinstance(snapshot.get("opportunities"), list):
        raise ValueError("Expected a schema-version-2 snapshot")
    collected = timestamp(snapshot["last_updated"])
    if not 0 <= (now - collected).total_seconds() <= 900:
        warnings.append("Snapshot is expired or future-dated; do not use it for current entries.")
    seen = set()
    rows = snapshot["opportunities"]
    for row in rows:
        label = f"{row.get('sport')} {row.get('player')} {row.get('stat')} {row.get('line')}"
        try:
            key = (row["sport"], row["player"], row["stat"], float(row["line"]), row["start_time"])
            if key in seen:
                raise ValueError("Duplicate player/stat/line/event")
            seen.add(key)
            if not math.isfinite(key[3]) or key[3] < 0 or key[3].is_integer():
                raise ValueError("Invalid or unmodeled integer line")
            if timestamp(row["start_time"]) <= collected:
                raise ValueError("Event had already started when snapshot was published")
            for field in ("prizepicks_observed_at", "sportsbook_observed_at"):
                if not -1 <= (collected - timestamp(row[field])).total_seconds() <= 900:
                    raise ValueError("Observation was stale or future-dated at publication")
            over, under = float(row["no_vig_over"]), float(row["no_vig_under"])
            if not all(math.isfinite(p) and 0 <= p <= 100 for p in (over, under)) or abs(over + under - 100) > 0.001:
                raise ValueError("Invalid consensus probabilities")
            quotes = row["book_comparisons"]
            if not quotes or len(quotes) != row["book_count"] or len({q["bookmaker"] for q in quotes}) != len(quotes):
                raise ValueError("Missing or duplicate sportsbook evidence")
            values = []
            for quote in quotes:
                a, b = implied(quote["over_odds"]), implied(quote["under_odds"])
                calculated = a / (a + b) * 100
                if abs(calculated - quote["no_vig_over"]) > 0.0002:
                    raise ValueError("Stored quote probability disagrees with its prices")
                values.append(calculated)
            values.sort()
            midpoint = len(values) // 2
            median = values[midpoint] if len(values) % 2 else (values[midpoint - 1] + values[midpoint]) / 2
            if abs(median - over) > 0.0002:
                raise ValueError("Consensus is not the median of contributing quotes")
            if row.get("payout_verified"):
                raise ValueError("Snapshot incorrectly claims account payout verification")
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            errors.append({"market": label, "problem": str(exc)})
    for check in checks:
        result = {k: check[k] for k in ("sport", "player", "stat", "line", "observed_at")}
        candidates = [r for r in rows if all(r.get(k) == check.get(k) for k in ("sport", "player", "stat", "start_time"))]
        if len(candidates) != 1:
            result["status"] = "not_comparable"
            result["reason"] = "No unique accepted comparison for this player/stat/event; this does not prove a source error."
        elif not check.get("board_refreshed") or abs((timestamp(check["observed_at"]) - timestamp(candidates[0]["prizepicks_observed_at"])).total_seconds()) > 300:
            result["status"] = "unverified"
            result["reason"] = "Board was not refreshed, or observations are more than five minutes apart."
        else:
            result["feed_line"] = candidates[0]["line"]
            result["status"] = "matched" if float(check["line"]) == float(result["feed_line"]) else "mismatched"
            result["reason"] = "A spot-check of one account and moment, not a guarantee for other users."
        manual.append(result)
    record_lag = 0
    unknown_record_time = 0
    for row in rows:
        try:
            if (collected - timestamp(row["provider_updated_at"])).total_seconds() > 900:
                record_lag += 1
        except (KeyError, ValueError, TypeError):
            unknown_record_time += 1
    if record_lag:
        warnings.append(f"{record_lag} rows have a feed-record timestamp more than 15 minutes before collection. This is record-level metadata, not a certified per-book quote timestamp.")
    counts = Counter(r["sport"] + ": " + r["stat"] for r in rows)
    return {
        "report_version": 1,
        "audited_at": now.isoformat(),
        "snapshot_collected_at": collected.isoformat(),
        "collection_day_pacific": collected.astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat(),
        "integrity_passed": not errors,
        "comparison_count": len(rows),
        "market_counts": dict(sorted(counts.items())),
        "feed_records_older_than_15m": record_lag,
        "feed_records_with_unknown_time": unknown_record_time,
        "unmatched_count": len(snapshot.get("unmatched", [])),
        "source_warnings": snapshot.get("source_info", {}).get("warnings", []),
        "errors": errors, "warnings": warnings, "manual_checks": manual,
        "manual_check_counts": dict(Counter(c["status"] for c in manual)),
        "limits": "Arithmetic/schema checks do not independently verify lines, quote freshness, payouts, profitability, or access from other networks. Multi-day coverage requires distinct collection dates; repeated audits of one snapshot do not count as new days.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=DATA_DIR / "opportunities.json")
    parser.add_argument("--checks", type=Path, help="Optional public PrizePicks observations; see README")
    parser.add_argument("--report-dir", type=Path, default=DATA_DIR / "validation")
    args = parser.parse_args()
    report = audit(json.loads(args.snapshot.read_text()), json.loads(args.checks.read_text()) if args.checks else [])
    args.report_dir.mkdir(parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("audit-%Y%m%dT%H%M%S%fZ.json")
    (args.report_dir / name).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    days = set()
    for path in args.report_dir.glob("audit-*.json"):
        prior = json.loads(path.read_text())
        if prior.get("integrity_passed"):
            days.add(prior["collection_day_pacific"])
    print(json.dumps({"report": str(args.report_dir / name), "integrity_passed": report["integrity_passed"], "distinct_collection_days": sorted(days), "manual_checks": report["manual_check_counts"], "warnings": report["warnings"]}))
    raise SystemExit(0 if report["integrity_passed"] and not report["manual_check_counts"].get("mismatched") else 1)


if __name__ == "__main__":
    main()
