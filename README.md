# PropShop

A local React dashboard that compares PrizePicks lines with sportsbook over/under prices and ranks estimated edges. Python collects the free [ScoresAndOdds prop comparisons](https://www.scoresandodds.com/nfl/props), validates exact event/line matches, calculates no-vig probabilities, and publishes a snapshot served by Express.

## Working data path

The default collector uses the same public comparison request as ScoresAndOdds' free **Odds Compare** drawer. Its response includes PrizePicks main lines and prices from FanDuel, DraftKings, BetMGM, Caesars, bet365, BetRivers, Hard Rock and Fanatics. It does not require a sportsbook login or API key. No premium projections, account data, affiliate links, or betting actions are used.

A successful October 19, 2026 run at 4:56 PM Pacific retrieved **122 PrizePicks lines and 509 sportsbook quotes**, producing **98 exact-line comparisons across NFL, NHL and MLB**, including two above the standard-payout model's break-even rate. Another 24 collected lines lacked an estimate: 19 integer lines requiring tie modeling and five without an unambiguous exact-line quote. Those counts describe that run, not guaranteed future coverage or profitability. The source had no NBA props published at the time.

**PrizePicks lines are reported by a third party.** The source does not certify your account's payout, promotions, or Goblin/Demon status. Published entry models are conditional on standard Player Picks payouts; the dashboard also supports a complete user-entered payout schedule. Confirm both the line and payout in PrizePicks before relying on an estimated edge. Prices may move or the source may lag: a source refresh does not guarantee the underlying sportsbook just updated its quote.

## Run locally

Requires macOS or Linux (the collector uses POSIX file locking), Python 3.9+ and Node 20+. The default public collector uses the Python standard library; no browser installation is required.

```bash
npm ci --prefix server
npm ci --prefix client
npm run build --prefix client
PORT=3011 node server/server.js
```

Open http://localhost:3011 and click **Collect fresh lines**. The API serves the built React dashboard. The server binds to loopback, with no public authentication system. For frontend development, use the API's default port 3001 and `npm start --prefix client`; the development proxy targets port 3001.

Standalone collection:

```bash
python3 daily_scraper.py
# Limit collection if desired:
python3 daily_scraper.py --sports NFL --max-events 5
```

The collector discovers public market categories and game IDs, checks schedule start times for today and tomorrow, and makes bounded requests with three workers and at least 350 ms between request starts. Access denials/rate limits stop new requests; requests already in flight may finish. There are no retries, proxy rotation or challenge automation. NBA/NFL/MLB/NHL are supported only when the source actually publishes relevant props.

Configuration uses exported environment variables, not automatic `.env` loading:

| Variable | Purpose |
| --- | --- |
| `PROPSHOP_SOURCE=public` | Default: public ScoresAndOdds comparison feed |
| `PROPSHOP_SPORTS=NBA,NFL,MLB,NHL` | Leagues to collect |
| `PYTHON=/absolute/path/to/python` | Interpreter override; otherwise `.venv/bin/python`, then `python3` |
| `PROPSHOP_DATA_DIR=/absolute/path` | Snapshot/status location |
| `PORT=3001` | API/static dashboard port; use 3011 if 3001 is occupied |

`--max-events` limits total upcoming games (1–100, default 20). The API stops a collection after ten minutes. Snapshots expire after 15 minutes and started events are excluded. Collection is on demand; polling the local API does not fetch third-party prices. No recurring schedule is installed automatically.

## Coverage and dashboard controls

The dashboard shows accepted exact-line comparisons, not the complete PrizePicks board. Collection covers supported full-game stat categories discovered on the source pages, within the configured event limit and 48-hour window. Markets missing from the feed, unsupported stat names, integer lines, and quotes at different lines do not produce comparison rows. The reported sportsbook quote count includes quotes across books and lines; it is not a count of unique player props.

**All accepted comparisons are shown by default**, including rows below the selected model's break-even probability. Enable **Positive edge only** to hide negative/zero estimates. Filter by sport, stat category, player, or minimum edge. Earlier versions enabled the positive-only filter by default, which hid most comparisons. Selecting another entry model changes each row's threshold, edge and illustrative entry ROI. The summary's **Above model break-even** count uses the best eligible model, so it can differ from the filtered table using your selected model.

The **Over/Under percentages** estimate each side from sportsbook prices. **Edge** is the difference from the chosen model's break-even rate, in percentage points. Expand **Sportsbook quotes** to inspect the contributing prices and number of books; a single-book comparison has less independent market evidence. Collection status and coverage warnings explain unavailable sources or leagues. Expand **Coverage** to see per-league/category collection counts, unsupported categories, and collected lines without an estimate. These lines have an explicit reason and no invented probability. The collector recognizes 16 published NFL categories, 12 MLB categories and five NHL categories when their menus publish them; a supported category may still return zero PrizePicks lines. NBA collection remains dependent on source publication. First/last touchdown scorer markets remain unsupported because they are not ordinary two-sided totals. Full PrizePicks coverage and automatic account-specific payout verification remain unfinished.

## What the percentages mean

For each sportsbook at the **exact PrizePicks line**, convert both prices to implied probabilities and normalize to remove that book's margin:

```text
no_vig_over = implied_over / (implied_over + implied_under)
no_vig_under = 1 - no_vig_over
```

The displayed consensus is the median over probability across eligible books, with under equal to one minus over. This prevents selecting only the most optimistic sportsbook. Single-book estimates are labeled. Expand **Sportsbook quotes** to see each book's over/under prices and over probability. Different lines are never interpolated.

In the default public data path, matching requires league, normalized player, explicit stat alias, numeric line, full-game period, start time and shared provider event ID. Ambiguous duplicate book quotes, incomplete/invalid prices, unavailable lines, unknown markets, started events, and observations retrieved more than 15 minutes ago are excluded. Integer lines are excluded because ties need a separate settlement model.

A market percentage is an estimate from offered prices, not a measured true win rate.

## Edge and entry models

```text
edge (percentage points) = consensus win percentage - model break-even percentage
illustrative entry ROI = expected payout for n independent, equally likely legs - 1
```

Power models include the all-hit payout. Flex models include every partial-hit payout, including returns below the entry fee. Break-even thresholds are calculated from those complete payout tables rather than hard-coded rounded rates.

Entry ROI describes an entire hypothetical entry whose legs all have the displayed probability. It is not one prop's expected return, a selected real lineup, or a guarantee. The project does not model correlations, actual entry eligibility, leaderboard payouts, account-specific offers, DNPs/reboots, or Early Payout.

### Verified PrizePicks payout schedules

**Last manually verified: October 19, 2026 (America/Los_Angeles).** Official references: [Payouts](https://www.prizepicks.com/help-center/payouts) and [Potential Outcomes](https://www.prizepicks.com/help-center/potential-outcomes); both pages displayed an October 19, 2026 update date when checked.

The following table is the **standard Player Picks minimum-guarantee schedule** modeled in `analysis.PAYOUTS`. All omitted hit counts return 0x. Multipliers describe total returned relative to the entry fee: a $10 entry returning 3x pays $30 total ($20 net profit); 1x returns the entry fee, and 0.4x returns $4 ($6 net loss).

| Entry model | Payout by number of correct picks | Equal-leg break-even probability |
| --- | --- | ---: |
| 2-Pick Power | 2/2: 3x | 57.7350% |
| 3-Pick Power | 3/3: 6x | 55.0321% |
| 4-Pick Power | 4/4: 10x | 56.2341% |
| 5-Pick Power | 5/5: 20x | 54.9280% |
| 6-Pick Power | 6/6: 37.5x | 54.6590% |
| 2-Pick Flex | 2/2: 2x; 1/2: 0.5x | 61.8034% |
| 3-Pick Flex | 3/3: 3x; 2/3: 1x | 57.7350% |
| 4-Pick Flex | 4/4: 6x; 3/4: 1.5x | 55.0321% |
| 5-Pick Flex | 5/5: 10x; 4/5: 2x; 3/5: 0.4x | 54.2525% |
| 6-Pick Flex | 6/6: 25x; 5/6: 2x; 4/6: 0.4x | 54.2060% |

**These probabilities are calculated by PropShop, not quoted by PrizePicks.** They solve `expected total return = 1` assuming every leg has the same win probability, legs are independent, and only the listed payout schedule applies. They are not a player's hit rate or a price offered on an individual prop. Figures are rounded for display; the engine uses the calculated unrounded thresholds.

For Power, `p = multiplier ** (-1 / pick_count)`. For Flex, PropShop includes every outcome in `sum(C(n,k) * p**k * (1-p)**(n-k) * payout[k]) = 1`. Looking only at Flex's all-hit multiplier produces the wrong threshold.

### Check your actual entry payout in the dashboard

Expand **Check the payout behind your edge estimate** to inspect every outcome of the selected model, including partial Flex returns and zero returns. The API exposes the standard schedule's manual verification date and source. Projection type does not verify an account's payout: collected rows remain `payout_verified: false`, including directly collected standard projections.

If the actual PrizePicks entry differs, select **Enter the payout shown for my entry**, copy total-return multipliers for every correct-pick count, and confirm that you copied the complete schedule. A $10 entry returning $30 total uses 3x. The dashboard recalculates equal-leg break-even, edge and illustrative entry ROI from that schedule; sportsbook percentages stay unchanged. Incomplete, invalid or unconfirmed custom schedules hide estimates. Returns must be nonnegative and nondecreasing with correct picks, with the all-hit return above 1x and zero-hit return below 1x. Nonmonotone promotions and schedules outside these constraints are unsupported.

This is a user-confirmed calculation, not an account connection or independent verification. It does not verify that the displayed players can be combined into the actual entry, or account for correlations, DNPs, ties, fees or leaderboard awards. The form applies one hypothetical schedule to the board for comparison. Values remain only in the current page session, reset when switching entry model or reloading, and are never sent to the server. The summary's positive count continues to use published standard models; custom values affect the comparison table only.

### When the standard table does not apply

PrizePicks' [Payouts explanation](https://www.prizepicks.com/help-center/payouts) says entry-specific amounts can differ because of promotions, bonus lineups, pick combinations, special projections, mixed Player/Team entries, and other disclosed factors. DNPs, Reboots and ties can also change settlement. **The payout schedule displayed for the actual entry controls; this table does not verify account-specific eligibility or payout.**

[Demons and Goblins](https://www.prizepicks.com/demons-and-goblins) can alter payouts in either direction. Do not reuse a standard threshold for a modified entry without its complete payout schedule. The public odds feed does not certify projection modifiers.

[Leaderboard winnings](https://www.prizepicks.com/help-center/potential-outcomes) are separate from the modeled minimum guarantee: the published standard six-pick leaderboard amounts are 25x Power and 12.5x Flex, versus the minimum-guarantee all-hit amounts of 37.5x and 25x above. Leaderboard ties can split prizes; eligible awards use the higher amount, not their sum. PropShop does not estimate leaderboard returns.

### Keeping the numbers current

Payout verification is manual. **Collect fresh lines refreshes source lines and sportsbook prices; it does not recheck PrizePicks' payout rules.**

When a published standard schedule changes:

1. Recheck both official sources above and the actual product/entry details; record the verification date and applicable schedule in this README and `analysis.PAYOUT_VERIFIED_AT`.
2. Update the complete hit-count mapping in `analysis.PAYOUTS`, including partial Flex returns. Do not change only the top multiplier or paste a rounded break-even percentage.
3. Recalculate the README table from `analysis.BET_TYPES`. `threshold()` derives break-even probabilities from the full mapping.
4. Run `python3 -m unittest discover -s tests -v`, then collect a new snapshot. Saved snapshots contain their calculated models; reading an old snapshot does not recalculate it after a payout-code change.

This review confirmed the existing modeled schedules; no payout constant needed changing on October 19, 2026.

## Optional direct browser adapters

The older direct PrizePicks/FanDuel route remains experimental and is **not needed by the default data path**. It was blocked by source restrictions during testing. It has not been verified end to end.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python daily_scraper.py --source browser --headed --timeout 300
```

This route uses a dedicated persistent profile at ignored `data/browser-profile/`, so a successful manual login can survive later runs. `PROPSHOP_PROFILE_DIR` overrides its path. This profile contains private session cookies: do not upload or share it. It never reads or copies your main Chrome profile. `PROPSHOP_HEADED=1` shows the browser; complete any verification yourself. Restrictions stop collection. There are no stealth scripts, fake geolocation, or automated CAPTCHA actions.

`PROPSHOP_SAVE_RAW=1` optionally saves direct-browser public response payloads for parser debugging; the default public collector does not persist raw payloads.

## Reliability and API

Collection has an API process lock and a POSIX file lock for CLI overlap. Failed collections preserve the last successful snapshot. Files are published with temporary-file/atomic replacement. Schema checks reject legacy fake-result formats. No unavailable-data path falls back to sample bets.

| Endpoint | Response |
| --- | --- |
| `GET /health` | Server health |
| `GET /api/opportunities` | Fresh comparisons, unmatched lines/reasons, source/coverage, payout verification metadata, summary, collection state |
| `GET /api/opportunities/:id` | Fresh row or 404 |
| `GET /api/stats` | Summary |
| `POST /api/trigger-scrape` | 202 accepted, 409 running, or explicit failure |
| `GET /api/scrape-status` | `idle`, `running`, `succeeded`, `failed`, or `interrupted` |

## Verification

```bash
python3 -m unittest discover -s tests -v
node --test server/server.test.js
CI=true npm test --prefix client -- --watchAll=false --runInBand
npm run build --prefix client
```

Tests use synthetic fixtures confined to tests. They cover odds validation, no-vig math, complete Flex payouts, consensus across same-line books, provider event identity/periods, source provenance, exclusion of premium fields, access-denial handling, stale/started rows, snapshot preservation, job lifecycle, model/stat filtering, unmatched-line expiry, custom payout validation/confirmation/reset, unchanged sportsbook probabilities, and empty states. Live collection and the dashboard refresh button are checked separately against real public data.

## Remaining limitations

The public endpoint is an implementation detail of another site, not a contracted API with an uptime guarantee. Its schema, availability, or permitted access can change. Source coverage is partial and third-party lines can lag. The dashboard shows provenance and source warnings rather than claiming complete market coverage.

Before public deployment, add authentication, operational monitoring, and data-use arrangements suitable for the intended use. The repository inherited tracked `node_modules/` directories; install from package lockfiles and keep future dependency housekeeping separate.
