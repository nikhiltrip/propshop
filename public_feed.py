"""Collect the free ScoresAndOdds comparison tables, without account data.

Uses the same public market-comparison request as the free Odds Compare drawer.
Only lines, available over/under prices, teams and schedule metadata are read.
Premium projections and other paid analysis fields are never used or persisted.
"""

import gzip
from html.parser import HTMLParser
from http.client import HTTPException
import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from analysis import canonical_stat, parse_time, utc_now
from collectors import CollectionError

SITE = "https://www.scoresandodds.com"
# Public endpoint observed in the site's global.js and verified against its drawer.
COMPARISON = (
    "https://rga51lus77.execute-api.us-east-1.amazonaws.com/prod/market-comparison"
)
SPORTSBOOKS = {
    "fanduel": "FanDuel",
    "draftkings": "DraftKings",
    "betmgm": "BetMGM",
    "caesars": "Caesars",
    "bet365": "bet365",
    "riverscasino": "BetRivers",
    "hardrock": "Hard Rock",
    "fanatics": "Fanatics",
}


# Exact labels verified on the public category pages on 2026-10-19.
# Only request categories that also appear in the current league's menu.
PATH_MARKETS = {
    "passing-yards": "passing yards", "rushing-yards": "rushing yards",
    "receiving-yards": "receiving yards", "receptions": "receptions",
    "points": "points", "rebounds": "rebounds", "assists": "assists",
    "3-pointers": "3 pointers", "strikeouts": "strikeouts", "hits": "hits",
    "shots-on-goal": "shots on goal", "saves": "saves",
    "completions": "completions", "interceptions": "interceptions",
    "kicking-points": "kicking points", "longest-completion": "longest completion",
    "longest-reception": "longest reception", "longest-rush": "longest rush",
    "pass-attempts": "pass attempts", "passing-&-rushing-yards": "passing & rushing yards",
    "passing-tds": "passing tds", "rush-attempts": "rush attempts",
    "rushing-&-receiving-yards": "rushing & receiving yards", "touchdowns": "touchdowns",
    "goals": "goals", "blocked-shots": "blocked shots",
    "earned-runs-allowed": "earned runs allowed", "hits,-runs-&-rbis": "hits, runs & rbis",
    "hits-allowed": "hits allowed", "home-runs": "home runs", "outs": "outs",
    "runs-batted-in": "runs batted in", "singles": "singles", "steals": "steals",
    "total-bases": "total bases", "walks-allowed": "walks allowed",
}


def discover_markets(parser):
    supported = {stat for ev, stat in parser.markets if ev and canonical_stat(stat)}
    unsupported = set()
    for ev, path in parser.markets:
        if ev:
            continue
        slug = path.rsplit("/", 1)[-1]
        if slug in PATH_MARKETS:
            supported.add(PATH_MARKETS[slug])
        else:
            unsupported.add(slug)
    return sorted(supported), sorted(unsupported)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events = []
        self.markets = set()
        self.json_script = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.json_script = True
            self.parts = []
        if (
            attrs.get("data-role") == "chassis"
            and attrs.get("data-event")
            and attrs.get("data-market")
        ):
            self.markets.add((attrs["data-event"], attrs["data-market"]))
        endpoint = attrs.get("data-endpoint") or ""
        # Stat labels/paths are discovered from the public prop picker, not guessed.
        if "/props/" in endpoint:
            self.markets.add(("", endpoint))

    def handle_data(self, data):
        if self.json_script:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.json_script:
            try:
                items = json.loads("".join(self.parts))
                if not isinstance(items, list):
                    items = [items]
                self.events.extend(
                    x
                    for x in items
                    if isinstance(x, dict) and x.get("@type") == "SportsEvent"
                )
            except (ValueError, TypeError):
                pass
            self.json_script = False


def parse_schedule(html, sport):
    parser = PageParser()
    parser.feed(html)
    rows = []
    for event in parser.events:
        try:
            # Explicit event ID and offset-aware start time from public JSON-LD.
            if event.get("eventStatus") not in (
                "https://schema.org/EventScheduled",
                "https://schema.org/EventRescheduled",
            ):
                continue
            start = parse_time(event["startDate"])
            event_id = str(event["identifier"])
            if (
                not event_id.isdigit()
                or urlparse(event["url"]).hostname != "www.scoresandodds.com"
            ):
                continue
            home = event["homeTeam"]["name"].split()[0]
            away = event["awayTeam"]["name"].split()[0]
            rows.append(
                {
                    "id": f"{sport.lower()}/{event_id}",
                    "sport": sport.upper(),
                    "start_time": start.isoformat(),
                    "event": event["name"],
                    "home": home,
                    "away": away,
                    "url": event["url"],
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return rows


class PublicClient:
    """Bounded requests; no retries on access denials, no persistent raw payloads."""

    def __init__(self, timeout=90):
        self.deadline = time.monotonic() + timeout
        self.lock = threading.Lock()
        self.last_request = 0.0
        self.blocked = threading.Event()

    def get(self, url):
        # Hosts are fixed in code. There is no arbitrary-URL proxy endpoint.
        if urlparse(url).hostname not in (
            "www.scoresandodds.com",
            "rga51lus77.execute-api.us-east-1.amazonaws.com",
        ):
            raise CollectionError("Unexpected public data host")
        with self.lock:
            if self.blocked.is_set():
                raise CollectionError(
                    "Public feed denied access or requested a pause; no further requests were sent."
                )
            delay = 0.35 - (time.monotonic() - self.last_request)
            if delay > 0:
                time.sleep(delay)
            remaining = self.deadline - time.monotonic()
            if self.blocked.is_set():
                raise CollectionError("Public feed access denied; no further requests sent.", "access_denied")
            if remaining <= 0:
                raise CollectionError("Public collection time limit reached; no further requests sent.", "deadline")
            self.last_request = time.monotonic()
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": "PropShop/2.0 (personal market comparison)",
                    "Accept": "text/html,application/json",
                },
            )
            with urlopen(request, timeout=min(10, remaining)) as response:
                body = response.read(8 * 1024 * 1024)
                if body[:2] == b"\x1f\x8b":
                    body = gzip.decompress(body)
                return body.decode("utf-8")
        except HTTPError as error:
            if error.code in (401, 403, 429):
                self.blocked.set()
            raise CollectionError(
                f"Public comparison feed returned HTTP {error.code}; collection stopped for this request.",
                "access_denied" if error.code in (401, 403, 429) else "http_error",
            ) from None
        except (URLError, TimeoutError, UnicodeError, OSError, HTTPException):
            raise CollectionError(
                "Public comparison feed could not be reached.", "network_error"
            ) from None

    def market(self, event, stat):
        params = {"event": event, "market": stat, "t": int(time.time())}
        try:
            payload = json.loads(self.get(COMPARISON + "?" + urlencode(params)))
            if not isinstance(payload, dict) or not isinstance(payload.get("markets"), list):
                raise CollectionError("Public comparison schema changed: markets array missing.", "schema_changed")
            return payload
        except ValueError:
            raise CollectionError(
                "Public comparison feed returned invalid JSON.", "schema_changed"
            ) from None


def parse_comparison(payload, event, observed_at=None):
    observed_at = observed_at or utc_now()
    pp_rows, book_rows = [], []
    metadata = payload.get("event", {})
    if metadata.get("sport", "").upper() != event["sport"]:
        return [], []
    if {metadata.get("home", {}).get("key"), metadata.get("away", {}).get("key")} != {
        event["home"],
        event["away"],
    }:
        return [], []
    league, event_id = event["id"].split("/")
    for market in payload.get("markets", []):
        try:
            parts = market["id"].split(".")
            # Period 0 is the full-game drawer. Never compare quarters or halves.
            if (
                len(parts) != 5
                or parts[:3] != [league, event_id, "0"]
                or market.get("available") is not True
            ):
                continue
            stat = market["stat"]
            if not canonical_stat(stat):
                continue
            player = market["player"]
            name = f"{player['first_name']} {player['last_name']}".strip()
            if not name:
                continue
            prices = market.get("comparison", {})
            pp = prices.get("prizepicks")
            if not pp or pp.get("available") is not True:
                continue
            line = float(pp["value"])
            if not math.isfinite(line) or line < 0:
                continue
            # Source does not certify Goblin/Demon/discount status. This is an
            # explicitly conditional standard-payout model, never verified eligibility.
            base = {
                "player": name,
                "sport": event["sport"],
                "stat": stat,
                "line": line,
                "start_time": event["start_time"],
                "period": "full_game",
                "observed_at": observed_at,
                "event_id": event["id"],
                "event": event["event"],
                "home_team": event["home"],
                "away_team": event["away"],
                "source_url": event["url"],
                "source": "scoresandodds",
                "provider_updated_at": (
                    datetime.fromtimestamp(
                        float(market["date"]), timezone.utc
                    ).isoformat()
                    if market.get("date")
                    else None
                ),
            }
            pp_rows.append(
                {
                    **base,
                    "variant": "provider_main",
                    "projection_id": market["id"],
                    "payout_verified": False,
                }
            )
            for key, label in SPORTSBOOKS.items():
                quote = prices.get(key)
                if not quote or quote.get("available") is not True:
                    continue
                try:
                    book_rows.append(
                        {
                            **base,
                            "line": float(quote["value"]),
                            "over_odds": float(quote["over"]),
                            "under_odds": float(quote["under"]),
                            "bookmaker": key,
                            "bookmaker_name": label,
                        }
                    )
                except (KeyError, TypeError, ValueError):
                    continue
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
    return pp_rows, book_rows


def collect_public(sports, data_dir, max_events=20, timeout=90):
    client = PublicClient(timeout)
    now = datetime.now(timezone.utc)
    today = now.astimezone(ZoneInfo("America/Los_Angeles")).date()
    coverage, errors, events, market_names = [], [], {}, {}
    for sport in sports:
        supported = set()
        try:
            html = client.get(f"{SITE}/{sport.lower()}/props")
            parser = PageParser()
            parser.feed(html)
            supported, unsupported = discover_markets(parser)
            market_names[sport] = sorted(supported)
            for day in [today, today + timedelta(days=1)]:
                html = client.get(
                    f"{SITE}/{sport.lower()}?" + urlencode({"date": day.isoformat()})
                )
                for event in parse_schedule(html, sport):
                    start = parse_time(event["start_time"])
                    if now < start <= now + timedelta(hours=48):
                        events[event["id"]] = event
            coverage.append(
                {
                    "sport": sport,
                    "markets": sorted(supported),
                    "unsupported_markets": unsupported,
                    "status": "available" if supported else "no_public_props",
                }
            )
        except CollectionError as error:
            errors.append({"sport": sport, "message": str(error), "code": error.code})
    # Give every available league a turn before spending the event budget on one league.
    queues = {sport: sorted((e for e in events.values() if e["sport"] == sport and market_names.get(sport)), key=lambda e: parse_time(e["start_time"])) for sport in sports}
    selected = []
    while len(selected) < max_events and any(queues.values()):
        for sport in sports:
            if queues[sport] and len(selected) < max_events:
                selected.append(queues[sport].pop(0))
    pp_rows, book_rows = [], []
    jobs = [
        (event, stat)
        for event in selected
        for stat in market_names.get(event["sport"], [])
    ]

    def fetch(job):
        event, stat = job
        payload = client.market(event["id"], stat)
        parsed = parse_comparison(payload, event)
        metadata = payload.get("event", {})
        if payload["markets"] and (metadata.get("sport", "").upper() != event["sport"] or
            {metadata.get("home", {}).get("key"), metadata.get("away", {}).get("key")} != {event["home"], event["away"]}):
            raise CollectionError("Comparison event identity does not match schedule.", "event_mismatch")
        offered = sum(isinstance(m, dict) and m.get("comparison", {}).get("prizepicks", {}).get("available") is True for m in payload["markets"])
        if offered and not parsed[0]:
            raise CollectionError("Available PrizePicks markets failed parser validation.", "schema_changed")
        return parsed, len(payload["markets"])

    returned_markets = 0
    completed_jobs = 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch, job): job for job in jobs}
        for future in as_completed(futures):
            event, stat = futures[future]
            try:
                (pp, books), count = future.result()
                returned_markets += count
                completed_jobs += 1
                pp_rows.extend(pp)
                book_rows.extend(books)
            except CollectionError as error:
                errors.append(
                    {"sport": event["sport"], "event_id": event["id"], "market": stat, "message": str(error), "code": error.code}
                )

    def dedupe(rows, fields):
        return list(
            {tuple(str(row.get(k)) for k in fields): row for row in rows}.values()
        )

    pp_rows = dedupe(pp_rows, ["event_id", "player", "stat", "line"])
    book_rows = dedupe(book_rows, ["event_id", "player", "stat", "line", "bookmaker"])
    for item in coverage:
        league = item["sport"]
        item["events_scanned"] = sum(e["sport"] == league for e in selected)
        item["prizepicks_lines"] = sum(r["sport"] == league for r in pp_rows)
        item["sportsbook_quotes"] = sum(r["sport"] == league for r in book_rows)
        item["market_counts"] = {
            stat: sum(r["sport"] == league and r["stat"] == stat for r in pp_rows)
            for stat in item["markets"]
        }
    # Store only non-sensitive coverage counts, not raw premium-containing payloads.
    info = {
        "source": "scoresandodds",
        "source_name": "ScoresAndOdds public comparisons",
        "events_scanned": len(selected),
        "events_available": len(events),
        "requests_for_markets": len(jobs),
        "completed_market_requests": completed_jobs,
        "returned_markets": returned_markets,
        "coverage": coverage,
        "warnings": errors,
        "collected_at": utc_now(),
        "prizepicks_line_verification": "Third-party main lines; confirm current line and payout in PrizePicks.",
    }
    if errors and (not pp_rows or not book_rows or any(e["code"] in ("access_denied", "schema_changed", "event_mismatch") for e in errors)):
        code = next((e["code"] for e in errors if e["code"] == "access_denied"), errors[0]["code"])
        raise CollectionError(f"Collection incomplete ({code}); see persisted source diagnostics. Last successful snapshot retained.", code, info)
    info["availability"] = "available" if pp_rows and book_rows else "empty"
    info["empty_reason"] = None if info["availability"] == "available" else (
        "No upcoming games with published supported markets." if not jobs else
        "The source returned no available PrizePicks/two-sided sportsbook pairs for the selected games."
    )
    return pp_rows, book_rows, info
