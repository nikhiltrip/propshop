# PropShop

A local React dashboard that compares PrizePicks lines with sportsbook over/under prices and ranks estimated edges. Python collects the free [ScoresAndOdds prop comparisons](https://www.scoresandodds.com/nfl/props), validates exact event/line matches, calculates no-vig probabilities, and publishes a snapshot served by Express.

## Working data path

The default collector uses the same public comparison request as ScoresAndOdds' free **Odds Compare** drawer. Its response includes PrizePicks main lines and prices from FanDuel, DraftKings, BetMGM, Caesars, bet365, BetRivers, Hard Rock and Fanatics. It does not require a sportsbook login or API key. No premium projections, account data, affiliate links, or betting actions are used.

A successful October 19, 2026 run retrieved **72 PrizePicks lines and 267 sportsbook quotes**, producing **53 exact-line comparisons across NFL, NHL and MLB**, including one above the standard-payout model's break-even rate. Those counts describe that run, not guaranteed future coverage or profitability. The source had no NBA props published at the time.

**PrizePicks lines are reported by a third party.** The source does not certify your account's payout, promotions, or Goblin/Demon status. Every entry model is conditional on standard Player Picks payouts. Confirm both the line and payout in PrizePicks before relying on an estimated edge. Prices may move or the source may lag: a source refresh does not guarantee the underlying sportsbook just updated its quote.

## Run locally

Requires Python 3.9+ and Node 20+. The default public collector uses the Python standard library; no browser installation is required.

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

The collector discovers public market categories and game IDs, checks schedule start times for today and tomorrow, and makes bounded requests with three workers and at least 350 ms between request starts. Access denials/rate limits stop subsequent requests. There are no retries, proxy rotation or challenge automation. NBA/NFL/MLB/NHL are supported only when the source actually publishes relevant props.

Configuration uses exported environment variables, not automatic `.env` loading:

| Variable | Purpose |
| --- | --- |
| `PROPSHOP_SOURCE=public` | Default: public ScoresAndOdds comparison feed |
| `PROPSHOP_SPORTS=NBA,NFL,MLB,NHL` | Leagues to collect |
| `PYTHON=/absolute/path/to/python` | Interpreter override; otherwise `.venv/bin/python`, then `python3` |
| `PROPSHOP_DATA_DIR=/absolute/path` | Snapshot/status location |
| `PORT=3001` | API/static dashboard port; use 3011 if 3001 is occupied |

`--max-events` limits total upcoming games (1–100, default 20). The API stops a collection after ten minutes. Snapshots expire after 15 minutes and started events are excluded. Collection is on demand; polling the local API does not fetch third-party prices. No recurring schedule is installed automatically.

## What the percentages mean

For each sportsbook at the **exact PrizePicks line**, convert both prices to implied probabilities and normalize to remove that book's margin:

```text
no_vig_over = implied_over / (implied_over + implied_under)
no_vig_under = 1 - no_vig_over
```

The displayed consensus is the median over probability across eligible books, with under equal to one minus over. This prevents selecting only the most optimistic sportsbook. Single-book estimates are labeled. Expand **Sportsbook quotes** to see each book's over/under prices and over probability. Different lines are never interpolated.

Matching requires league, normalized player, explicit stat alias, numeric line, full-game period, start time and shared provider event ID. Ambiguous duplicate book quotes, incomplete/invalid prices, unavailable lines, unknown markets, started events, and observations retrieved more than 15 minutes ago are excluded. Integer lines are excluded because ties need a separate settlement model.

A market percentage is an estimate from offered prices, not a measured true win rate.

## Edge and entry models

```text
edge (percentage points) = consensus win percentage - model break-even percentage
illustrative entry ROI = expected payout for n independent, equally likely legs - 1
```

Power models include the all-hit payout. Flex models include every partial-hit payout, including returns below the entry fee. Break-even thresholds are calculated from those complete payout tables rather than hard-coded rounded rates.

Entry ROI describes an entire hypothetical entry whose legs all have the displayed probability. It is not one prop's expected return, a selected real lineup, or a guarantee. The project does not model correlations, actual entry eligibility, leaderboard payouts, account-specific offers, DNPs/reboots, or Early Payout.

Standard Player Picks minimum-guarantee payouts were checked against [PrizePicks Potential Outcomes](https://www.prizepicks.com/help-center/potential-outcomes) on October 19, 2026. Verify the actual payout shown in your account. Modified projections are not validated by the public feed and must not be treated as certified standard-payout picks.

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
| `GET /api/opportunities` | Fresh comparisons, source/coverage, summary, collection state |
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

Tests use synthetic fixtures confined to tests. They cover odds validation, no-vig math, complete Flex payouts, consensus across same-line books, provider event identity/periods, source provenance, exclusion of premium fields, access-denial handling, stale/started rows, snapshot preservation, job lifecycle, model switching and empty states. Live collection and the dashboard refresh button are checked separately against real public data.

## Remaining limitations

The public endpoint is an implementation detail of another site, not a contracted API with an uptime guarantee. Its schema, availability, or permitted access can change. Source coverage is partial and third-party lines can lag. The dashboard shows provenance and source warnings rather than claiming complete market coverage.

Before public deployment, add authentication, operational monitoring, and data-use arrangements suitable for the intended use. The repository inherited tracked `node_modules/` directories; install from package lockfiles and keep future dependency housekeeping separate.
