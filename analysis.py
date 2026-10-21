"""Exact-line comparison and transparent entry-model calculations (no browser deps)."""

import hashlib
import math
import statistics
import re
import unicodedata
from datetime import datetime, timezone

PAYOUT_VERIFIED_AT = "2026-10-19"
PAYOUT_SOURCE = "https://www.prizepicks.com/help-center/potential-outcomes"
# Standard Player Picks minimum guarantee, verified 2026-10-19.
PAYOUTS = {
    "2-Pick Power": {2: 3},
    "3-Pick Power": {3: 6},
    "4-Pick Power": {4: 10},
    "5-Pick Power": {5: 20},
    "6-Pick Power": {6: 37.5},
    "2-Pick Flex": {2: 2, 1: 0.5},
    "3-Pick Flex": {3: 3, 2: 1},
    "4-Pick Flex": {4: 6, 3: 1.5},
    "5-Pick Flex": {5: 10, 4: 2, 3: 0.4},
    "6-Pick Flex": {6: 25, 5: 2, 4: 0.4},
}


def normalize(value):
    return re.sub(
        r"[^a-z0-9]",
        "",
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode()
        .lower(),
    )


ALIASES = {
    "points": ["points", "pts", "player_points"],
    "rebounds": ["rebounds", "rebs", "player_rebounds"],
    "assists": ["assists", "asts", "player_assists"],
    "threes": [
        "3-pt made",
        "3-pointers made",
        "3 pointers",
        "made threes",
        "player_threes",
    ],
    "points_rebounds_assists": [
        "pts+rebs+asts",
        "points + rebounds + assists",
        "player_points_rebounds_assists",
    ],
    "points_rebounds": ["pts+rebs", "points + rebounds", "player_points_rebounds"],
    "points_assists": ["pts+asts", "points + assists", "player_points_assists"],
    "rebounds_assists": ["rebs+asts", "rebounds + assists", "player_rebounds_assists"],
    "passing_yards": ["pass yards", "passing yards", "player_pass_yds"],
    "rushing_yards": ["rush yards", "rushing yards", "player_rush_yds"],
    "receiving_yards": ["receiving yards", "rec yards", "player_reception_yds"],
    "receptions": ["receptions", "recs", "player_receptions"],
    "strikeouts": [
        "pitcher strikeouts",
        "strikeouts",
        "player_strikeouts",
        "pitcher_strikeouts",
    ],
    "hits": ["hits", "batter_hits"],
    "shots_on_goal": ["shots on goal", "player_shots_on_goal"],
    "saves": ["goalie saves", "saves", "player_total_saves"],
    "goals": ["goals"],
    "blocked_shots": ["blocked shots", "blocked-shots"],
    "completions": ["completions", "pass completions", "passing completions"],
    "pass_attempts": ["pass attempts", "passing attempts"],
    "rush_attempts": ["rush attempts", "rushing attempts", "rush atts"],
    "passing_tds": ["passing tds", "pass tds", "passing touchdowns"],
    "interceptions": ["interceptions", "interceptions thrown", "ints"],
    "kicking_points": ["kicking points", "kicker points"],
    "longest_completion": ["longest completion", "longest pass"],
    "longest_reception": ["longest reception"],
    "longest_rush": ["longest rush"],
    "passing_rushing_yards": ["passing & rushing yards", "pass+rush yds"],
    "rushing_receiving_yards": ["rushing & receiving yards", "rush+rec yds"],
    "touchdowns": ["touchdowns", "rush+rec tds"],
    "earned_runs_allowed": ["earned runs allowed", "earned runs"],
    "hits_runs_rbis": ["hits, runs & rbis", "hits+runs+rbis"],
    "hits_allowed": ["hits allowed"],
    "home_runs": ["home runs"],
    "outs": ["outs", "pitching outs", "pitcher outs"],
    "runs_batted_in": ["runs batted in", "rbis"],
    "singles": ["singles"],
    "steals": ["steals", "stolen bases"],
    "total_bases": ["total bases"],
    "walks_allowed": ["walks allowed"],
}
STAT_LOOKUP = {
    normalize(alias): key
    for key, aliases in ALIASES.items()
    for alias in [key, *aliases]
}


def canonical_stat(value):
    # Explicit aliases only: points must never match points+rebounds.
    return STAT_LOOKUP.get(normalize(value))


def parse_time(value):
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    return dt.astimezone(timezone.utc)


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def american_to_probability(odds):
    odds = float(odds)
    if not math.isfinite(odds) or abs(odds) < 100:
        raise ValueError("Invalid American odds")
    return (100 / (odds + 100) if odds > 0 else -odds / (-odds + 100)) * 100


def calculate_no_vig_probability(over_odds, under_odds):
    over, under = american_to_probability(over_odds), american_to_probability(
        under_odds
    )
    return over / (over + under) * 100, under / (over + under) * 100


def expected_return(probabilities, payouts):
    """Poisson-binomial entry return, including stake, assuming independent legs."""
    distribution = [1.0]
    for p in probabilities:
        if not 0 <= p <= 1:
            raise ValueError("Probability outside [0,1]")
        nxt = [0.0] * (len(distribution) + 1)
        for hits, chance in enumerate(distribution):
            nxt[hits] += chance * (1 - p)
            nxt[hits + 1] += chance * p
        distribution = nxt
    return sum(
        chance * payouts.get(hits, 0) for hits, chance in enumerate(distribution)
    )


def threshold(name):
    n = int(name[0])
    low, high = 0.0, 1.0
    for _ in range(70):
        mid = (low + high) / 2
        if expected_return([mid] * n, PAYOUTS[name]) < 1:
            low = mid
        else:
            high = mid
    return (low + high) / 2 * 100


BET_TYPES = {
    name: {
        "payout": max(p.values()),
        "min_win_pct": threshold(name),
        "type": name.split()[-1].lower(),
        "payouts": p,
    }
    for name, p in PAYOUTS.items()
}


def match_key(row):
    stat = canonical_stat(row.get("stat", ""))
    line = float(row["line"])
    if (
        not stat
        or not math.isfinite(line)
        or line < 0
        or not normalize(row.get("player", ""))
    ):
        raise ValueError("Unsupported market")
    if row.get("period") != "full_game":
        raise ValueError("Unsupported or unknown period")
    return (
        row["sport"].upper(),
        normalize(row["player"]),
        stat,
        line,
        parse_time(row["start_time"]).isoformat(),
    )


def compare(prizepicks, fanduel, now=None, max_age_seconds=900):
    now = now or datetime.now(timezone.utc)
    index, rejected = {}, 0
    for row in fanduel:
        try:
            key = match_key(row)
            age = (now - parse_time(row["observed_at"])).total_seconds()
            if not 0 <= age <= max_age_seconds or parse_time(row["start_time"]) <= now:
                raise ValueError("Old odds")
            calculate_no_vig_probability(row["over_odds"], row["under_odds"])
            index.setdefault(key, {}).setdefault(
                row.get("bookmaker", "fanduel"), []
            ).append(row)
        except (KeyError, TypeError, ValueError):
            rejected += 1
    results, seen, unmatched = [], set(), []
    for pp in prizepicks:
        try:
            key = match_key(pp)
            age = (now - parse_time(pp["observed_at"])).total_seconds()
            if (
                pp.get("variant") not in ("standard", "provider_main")
                or not 0 <= age <= max_age_seconds
                or parse_time(pp["start_time"]) <= now
            ):
                raise ValueError("Old or nonstandard projection")
            def without_estimate(reason):
                unmatched.append({
                    "id": hashlib.sha256(repr(key).encode()).hexdigest()[:16],
                    "player": pp["player"], "sport": pp["sport"],
                    "stat": pp["stat"], "line": float(pp["line"]),
                    "start_time": pp["start_time"], "observed_at": pp["observed_at"],
                    "reason": reason,
                })
            # Integer lines need a push/void model. Do not pretend P(win | no tie) is P(win).
            if float(pp["line"]).is_integer():
                without_estimate("Integer line: tie/settlement probabilities are not modeled.")
                raise ValueError("Push model required")
            candidate_groups = index.get(key, {})
            candidates = [
                rows[0]
                for rows in candidate_groups.values()
                if len(rows) == 1
                and (
                    not pp.get("event_id") or rows[0].get("event_id") == pp["event_id"]
                )
            ]
            if not candidates:
                without_estimate("No unambiguous, fresh two-sided sportsbook quote at this exact line.")
                raise ValueError("Missing or ambiguous event/market")
            if key in seen:
                continue
            seen.add(key)
            book_comparisons = []
            for quote in candidates:
                o, u = calculate_no_vig_probability(
                    quote["over_odds"], quote["under_odds"]
                )
                book_comparisons.append(
                    {
                        "bookmaker": quote.get("bookmaker", "fanduel"),
                        "name": quote.get("bookmaker_name", "FanDuel"),
                        "over_odds": quote["over_odds"],
                        "under_odds": quote["under_odds"],
                        "no_vig_over": round(o, 4),
                        "no_vig_under": round(u, 4),
                        "observed_at": quote["observed_at"],
                    }
                )
            # Median of available same-line books avoids selecting the most optimistic quote.
            over = statistics.median(b["no_vig_over"] for b in book_comparisons)
            under = 100 - over
            fd = min(
                candidates,
                key=lambda q: abs(
                    calculate_no_vig_probability(q["over_odds"], q["under_odds"])[0]
                    - over
                ),
            )
            direction, pct = ("over", over) if over >= under else ("under", under)
            models = []
            for name, info in BET_TYPES.items():
                models.append(
                    {
                        "type": name,
                        "edge": round(pct - info["min_win_pct"], 4),
                        "threshold": round(info["min_win_pct"], 4),
                        "equal_leg_roi_pct": round(
                            (
                                expected_return(
                                    [pct / 100] * int(name[0]), PAYOUTS[name]
                                )
                                - 1
                            )
                            * 100,
                            4,
                        ),
                    }
                )
            best = max(models, key=lambda m: m["edge"])
            results.append(
                {
                    "id": hashlib.sha256(repr(key).encode()).hexdigest()[:16],
                    "player": pp["player"],
                    "sport": pp["sport"],
                    "stat": pp["stat"],
                    "line": float(pp["line"]),
                    "fanduel_line": float(fd["line"]),
                    "sportsbook_line": float(fd["line"]),
                    "reference_bookmaker": fd.get("bookmaker_name", "FanDuel"),
                    "book_comparisons": book_comparisons,
                    "book_count": len(book_comparisons),
                    "payout_verified": False,
                    "projection_variant": pp.get("variant"),
                    "source_url": fd.get(
                        "source_url", "https://sportsbook.fanduel.com/"
                    ),
                    "provider_updated_at": fd.get("provider_updated_at"),
                    "direction": direction,
                    "over_odds": float(fd["over_odds"]),
                    "under_odds": float(fd["under_odds"]),
                    "no_vig_win_pct": round(pct, 4),
                    "no_vig_over": round(over, 4),
                    "no_vig_under": round(under, 4),
                    "edge": best["edge"],
                    "best_bet_type": best["type"],
                    "models": models,
                    "start_time": pp["start_time"],
                    "prizepicks_observed_at": pp["observed_at"],
                    "fanduel_observed_at": fd["observed_at"],
                    "sportsbook_observed_at": min(q["observed_at"] for q in candidates),
                    "event": fd.get("event", ""),
                    "home_team": pp.get("home_team"),
                    "away_team": pp.get("away_team"),
                    "prizepicks_url": "https://app.prizepicks.com/",
                    "fanduel_url": "https://sportsbook.fanduel.com/",
                }
            )
        except (KeyError, TypeError, ValueError):
            rejected += 1
    results.sort(key=lambda r: r["edge"], reverse=True)
    positive = [r for r in results if r["edge"] > 0]
    return {
        "schema_version": 2,
        "opportunities": results,
        "unmatched": list({row["id"]: row for row in unmatched}.values()),
        "payout_verification": {
            "standard_schedule_checked_at": PAYOUT_VERIFIED_AT,
            "source_url": PAYOUT_SOURCE,
            "account_entry_verified": False,
        },
        "last_updated": utc_now(),
        "models": BET_TYPES,
        "payout_source": PAYOUT_SOURCE,
        "stats": {
            "sportsbook_collected": len(fanduel),
            "books_collected": len({r.get("bookmaker", "fanduel") for r in fanduel}),
            "prizepicks_collected": len(prizepicks),
            "fanduel_collected": len(fanduel),
            "total_scanned": len(results),
            "plus_ev_found": len(positive),
            "rejected": rejected,
            "best_edge": max((r["edge"] for r in results), default=0),
        },
        "methodology": "Median proportional no-vig estimates across available exact-line sportsbooks. For provider main lines, payout eligibility is unverified and the standard-payout model is conditional. Edge is percentage points above an equal-probability, independent-leg entry break-even rate. Entry ROI is illustrative, not individual-pick ROI. Standard Player Picks minimum guarantee only; no leaderboard, promotions, ties, DNPs or correlation model.",
    }
