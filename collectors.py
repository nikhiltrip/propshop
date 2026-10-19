"""Public browser collection. Never automate CAPTCHAs or spoof location/identity."""

import asyncio
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse
from analysis import utc_now, canonical_stat


class CollectionError(RuntimeError):
    pass


def parse_prizepicks(payload, observed_at=None):
    observed_at = observed_at or utc_now()
    included = {
        (r["type"], str(r["id"])): r.get("attributes", {})
        for r in payload.get("included", [])
    }
    rows = []
    for item in payload.get("data", []):
        if item.get("type") != "projection":
            continue
        try:
            a, rel = item["attributes"], item["relationships"]

            def related(name):
                ref = rel.get(name, {}).get("data") or {}
                return included.get((ref.get("type"), str(ref.get("id"))), {})

            player, league = related("new_player"), related("league")
            # Only documented full-game leagues; never infer sport from a stat name.
            sport = league.get("name", "")
            if sport not in ("NBA", "NFL", "MLB", "NHL"):
                continue
            if (
                a.get("status") != "pre_game"
                or a.get("is_promo")
                or a.get("odds_type") != "standard"
            ):
                continue
            if a.get("projection_type", "Single Stat") != "Single Stat":
                continue
            stat = a["stat_type"]
            if not canonical_stat(stat):
                continue
            rows.append(
                {
                    "player": player["display_name"],
                    "sport": sport,
                    "stat": stat,
                    "line": float(a["line_score"]),
                    "start_time": a["start_time"],
                    "observed_at": observed_at,
                    "period": "full_game",
                    "variant": "standard",
                    "projection_id": str(item["id"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return rows


def parse_fanduel(payload, sport, observed_at=None):
    """Parse the event/market attachments delivered to the public FanDuel board."""
    observed_at = observed_at or utc_now()
    attachments = payload.get("attachments", {})
    events = {str(k): v for k, v in attachments.get("events", {}).items()}
    rows = []
    for market in attachments.get("markets", {}).values():
        try:
            event = events[str(market["eventId"])]
            if market.get("marketStatus") != "OPEN" or event.get("inPlay"):
                continue
            # Accept only explicit "Player - Stat" full-game markets.
            name = market["marketName"]
            if " - " not in name:
                continue
            player, stat = name.rsplit(" - ", 1)
            if not canonical_stat(stat):
                continue
            sides = {}
            for runner in market.get("runners", []):
                if runner.get("runnerStatus", "ACTIVE") != "ACTIVE":
                    continue
                match = re.fullmatch(
                    r"(?:"
                    + re.escape(player)
                    + r"\s+)?(Over|Under)\s+([0-9]+(?:\.[0-9]+)?)",
                    runner["runnerName"],
                    re.I,
                )
                if not match:
                    continue
                side, line = match[1].lower(), float(match[2])
                odds = runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
                sides.setdefault(line, {})[side] = float(odds)
            for line, prices in sides.items():
                if set(prices) == {"over", "under"}:
                    rows.append(
                        {
                            "player": player,
                            "sport": sport,
                            "stat": stat,
                            "line": line,
                            "over_odds": prices["over"],
                            "under_odds": prices["under"],
                            "start_time": event["openDate"],
                            "event": event.get("name", ""),
                            "observed_at": observed_at,
                            "period": "full_game",
                            "event_id": str(market["eventId"]),
                        }
                    )
        except (KeyError, TypeError, ValueError):
            continue
    return rows


async def collect_browser(sports, headed=False, timeout=90, max_events=20):
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise CollectionError(
            "Install requirements.txt and run python3 -m playwright install chromium."
        ) from None
    pp, fd, blocked = [], [], []
    event_sports = {}
    event_cache = {}

    def save_capture(source, payload):
        if os.getenv("PROPSHOP_SAVE_RAW") == "1":
            root = (
                Path(os.getenv("PROPSHOP_DATA_DIR", Path(__file__).parent / "data"))
                / "raw"
            )
            root.mkdir(parents=True, exist_ok=True)
            (root / (source + ".json")).write_text(json.dumps(payload))

    async with async_playwright() as p:
        # Dedicated profile retains only this app's session, never the user's main profile.
        profile = Path(
            os.getenv(
                "PROPSHOP_PROFILE_DIR",
                Path(__file__).parent / "data" / "browser-profile",
            )
        )
        profile.mkdir(parents=True, exist_ok=True, mode=0o700)
        context = await p.chromium.launch_persistent_context(
            str(profile), headless=not headed
        )
        page = await context.new_page()
        tasks = set()

        async def capture(response, source, sport=None):
            host = urlparse(response.url).hostname or ""
            if (
                source == "prizepicks"
                and (host == "prizepicks.com" or host.endswith(".prizepicks.com"))
                and "/projections" in response.url
            ):
                if response.status in (401, 403, 429):
                    blocked.append(
                        "PrizePicks blocked collection (HTTP %s). Open the board and complete any verification manually; then retry."
                        % response.status
                    )
                    return
                try:
                    payload = await response.json()
                    save_capture("prizepicks", payload)
                    rows = parse_prizepicks(payload)
                    print(
                        f'PrizePicks response: {len(payload.get("data", []))} records, {len(rows)} supported projections.',
                        flush=True,
                    )
                    pp.extend(rows)
                except Exception:
                    # Response bodies may disappear during navigation. No data is safer than guessed rows.
                    pass
            elif (
                source == "fanduel"
                and host.endswith(".fanduel.com")
                and "json" in response.headers.get("content-type", "")
            ):
                try:
                    payload = await response.json()
                    if isinstance(payload, dict) and "attachments" in payload:
                        save_capture("fanduel-" + sport, payload)
                    attachments = payload.get("attachments", {})
                    event_cache.update(attachments.get("events", {}))
                    merged = {
                        **payload,
                        "attachments": {**attachments, "events": event_cache},
                    }
                    rows = parse_fanduel(merged, sport)
                    fd.extend(
                        row
                        for row in rows
                        if event_sports.get(row["event_id"]) == sport
                    )
                except Exception:
                    # Response bodies may disappear during navigation. No data is safer than guessed rows.
                    pass

        def listen(source, sport=None):
            def handler(response):
                task = asyncio.create_task(capture(response, source, sport))
                tasks.add(task)
                task.add_done_callback(tasks.discard)

            return handler

        handler = listen("prizepicks")
        page.on("response", handler)
        try:
            await page.goto(
                "https://app.prizepicks.com/",
                wait_until="domcontentloaded",
                timeout=45000,
            )
            for _ in range(timeout):
                text = (await page.locator("body").inner_text()).lower()
                if (
                    "access is restricted" in text
                    or "access restricted" in text
                    or "access denied" in text
                ):
                    raise CollectionError(
                        "PrizePicks restricted this browser session. Collection stopped; no automated retries. Restore source access before trying again."
                    )
                if pp or (blocked and not headed):
                    break
                await asyncio.sleep(1)
            # Select each supported sport through normal visible board controls.
            if pp:
                for sport in sports:
                    button = page.get_by_role(
                        "tab",
                        name=re.compile(r"^" + sport + r"(?:\s+" + sport + r")?$"),
                    )
                    if await button.count() == 1:
                        await button.click(timeout=5000)
                        await asyncio.sleep(2)
            if tasks:
                await asyncio.gather(*list(tasks))
            if not pp:
                raise CollectionError(
                    blocked[0]
                    if blocked
                    else "PrizePicks returned no supported projections. The board may require manual verification, or its response schema has changed. No new results were published."
                )
            page.remove_listener("response", handler)
            for sport in sports:
                handler = listen("fanduel", sport)
                page.on("response", handler)
                await page.goto(
                    "https://sportsbook.fanduel.com/navigation/" + sport.lower(),
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                await asyncio.sleep(4)
                links = await page.locator("a[href]").evaluate_all(
                    "(els) => els.map(el => el.href)"
                )
                # Navigate visible event links only, within the FanDuel host.
                league_path = {
                    "NBA": "/basketball/nba/",
                    "NFL": "/football/nfl/",
                    "MLB": "/baseball/mlb/",
                    "NHL": "/hockey/nhl/",
                }[sport]
                links = list(
                    dict.fromkeys(
                        url
                        for url in links
                        if urlparse(url).hostname == "sportsbook.fanduel.com"
                        and urlparse(url).path.startswith(league_path)
                        and re.search(r"-[0-9]{6,}$", urlparse(url).path)
                    )
                )
                for url in links:
                    event_sports[urlparse(url).path.rsplit("-", 1)[-1]] = sport
                for url in links[:max_events]:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await asyncio.sleep(2)
                    text = (await page.locator("body").inner_text()).lower()
                    if (
                        "access is restricted" in text
                        or "access restricted" in text
                        or "access denied" in text
                    ):
                        raise CollectionError(
                            "FanDuel restricted this browser session. Collection stopped; restore source access before trying again."
                        )
                if tasks:
                    await asyncio.gather(*list(tasks))
                page.remove_listener("response", handler)
            if not fd:
                raise CollectionError(
                    "FanDuel returned no supported two-sided player markets. Manual verification, region access, or a parser update may be required. No new results were published."
                )
        finally:
            await context.close()

    def dedupe(rows, fields):
        return list({tuple(str(r.get(k)) for k in fields): r for r in rows}.values())

    return dedupe([r for r in pp if r["sport"] in sports], ["projection_id"]), dedupe(
        fd, ["sport", "event_id", "player", "stat", "line"]
    )
