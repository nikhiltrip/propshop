#!/usr/bin/env python3
"""Collect both real sources, match exact markets, and atomically publish a snapshot."""
import argparse
import asyncio
import fcntl
import json
import os
from pathlib import Path
import sys
import tempfile
from analysis import compare, utc_now
from collectors import CollectionError, collect_browser
from public_feed import collect_public

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("PROPSHOP_DATA_DIR", ROOT / "data"))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--headed",
        action="store_true",
        default=os.getenv("PROPSHOP_HEADED") == "1",
        help="Show normal browser; complete any verification yourself",
    )
    parser.add_argument(
        "--sports", default=os.getenv("PROPSHOP_SPORTS", "NBA,NFL,MLB,NHL")
    )
    parser.add_argument(
        "--source",
        choices=["public", "browser"],
        default=os.getenv("PROPSHOP_SOURCE", "public"),
    )
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--max-events", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300 or not 1 <= args.max_events <= 100:
        parser.error("timeout must be 1–300 seconds; max-events must be 1–100")
    sports = [s.strip().upper() for s in args.sports.split(",")]
    if not sports or any(s not in ("NBA", "NFL", "MLB", "NHL") for s in sports):
        parser.error("Supported sports: NBA,NFL,MLB,NHL")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / ".scrape.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another collection is already running.", file=sys.stderr)
            sys.exit(2)
        started = utc_now()
        status_path = DATA_DIR / "collection-status.json"
        atomic_json(status_path, {"state": "running", "started_at": started})
        try:
            if args.source == "public":
                pp, fd, source_info = collect_public(sports, DATA_DIR, args.max_events)
            else:
                pp, fd = asyncio.run(
                    collect_browser(sports, args.headed, args.timeout, args.max_events)
                )
                source_info = {
                    "source": "browser",
                    "source_name": "Direct browser collection",
                }
            result = compare(pp, fd)
            result["source"] = source_info["source"]
            result["source_info"] = source_info
            if not result["opportunities"]:
                raise CollectionError(
                    "Both sources returned data, but no fresh exact-line, full-game matches passed validation. Last successful snapshot retained."
                )
            atomic_json(DATA_DIR / "opportunities.json", result)
            atomic_json(
                status_path,
                {
                    "state": "succeeded",
                    "started_at": started,
                    "finished_at": utc_now(),
                    "message": f"Matched {len(result['opportunities'])} props.",
                },
            )
            print(json.dumps(result["stats"]))
        except Exception as exc:
            message = (
                str(exc)
                if isinstance(exc, CollectionError)
                else f"Collection failed ({type(exc).__name__}); check browser installation, connectivity, and parsers."
            )
            atomic_json(
                status_path,
                {
                    "state": "failed",
                    "started_at": started,
                    "finished_at": utc_now(),
                    "message": message,
                },
            )
            print(message, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
