# PropShop

A React dashboard for comparing standard PrizePicks player projections with FanDuel two-sided player-prop odds. Python collects public board responses, validates exact market matches, removes the bookmaker margin, and publishes a snapshot served by Express.

## Current state (October 19, 2026)

The analysis, snapshot pipeline, API lifecycle, and React production build have automated/local validation. **Live end-to-end collection has not been verified.** PrizePicks' direct public endpoint returned HTTP 403. The ordinary browser board loaded in one session, but the separate scraper browser was restricted after manual verification. No successful live snapshot was produced, and no real profitable bets are claimed.

The collection adapters need validation against successful current source responses once access is restored. They intentionally stop rather than disguise the browser, simulate location, solve challenges, or invent data. Having Playwright installed does not guarantee either site permits the browser session.

## Run locally

Requires Python 3.9+, Node 20+, npm, and a Playwright Chromium installation.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
npm ci --prefix server
npm ci --prefix client
npm run build --prefix client
PROPSHOP_HEADED=1 node server/server.js
```

Open http://localhost:3001. The API serves the built React app. `PORT=3011` selects a different port if needed. The server binds to loopback; this is a local tool with no public authentication system.

Click **Collect fresh lines** to launch the collector. Set `PROPSHOP_HEADED=1` to show the browser. If a site requests human verification, complete it yourself. If it restricts access after verification, stop and resolve access with the source. Repeated challenges are not a reliability strategy.

For frontend development, start the API on port 3001 and run `npm start --prefix client` in another terminal. React's development proxy targets port 3001.

Run collection directly:

```bash
.venv/bin/python daily_scraper.py --headed --sports NBA,NFL,MLB,NHL
```

Configuration uses exported environment variables, not automatic `.env` loading:

| Variable | Purpose |
| --- | --- |
| `PROPSHOP_HEADED=1` | Show the ordinary collection browser |
| `PROPSHOP_SPORTS=NBA,NFL` | Limit league navigation |
| `PYTHON=/absolute/path/to/python` | Override the collector interpreter; otherwise `.venv/bin/python`, then `python3` |
| `PROPSHOP_DATA_DIR=/absolute/path` | Override snapshot/status location |
| `PROPSHOP_SAVE_RAW=1` | Save public JSON payloads in ignored `data/raw/` for parser debugging |
| `PORT=3001` | API/static dashboard port |

CLI options also include `--timeout` (1–300 seconds for the initial PrizePicks response) and `--max-events` (1–100 events per league; default 20). The API terminates collection after ten minutes. No schedule is installed automatically. Daily-only collection is insufficient to keep a 15-minute snapshot fresh.

## Comparison rules

A match requires the same league, normalized player name, explicit stat alias, numeric line, full-game period, and timezone-aware event start time. Different start times are deliberately unmatched; they need source event-ID reconciliation rather than a guessed association. Ambiguous matches, incomplete odds, unknown periods/stats, started games, modified PrizePicks projections, and observations older than 15 minutes are excluded.

Both FanDuel prices must be available at the exact PrizePicks line. American prices are converted to implied probabilities, then normalized:

```text
no_vig_over = implied_over / (implied_over + implied_under)
no_vig_under = 1 - no_vig_over
```

These are **market probability estimates**, not measured true win rates. Integer lines are excluded because ties require a separate settlement/push model. There is no invented probability adjustment when a line changes: obtain fresh matching odds instead.

## Edge and payouts

Each selectable entry model has an equal-leg break-even probability calculated from its complete payout table. For Power entries only an all-hit outcome pays. Flex calculations include every partial-hit payout, including payouts below the original entry fee.

```text
edge (percentage points) = no-vig win percentage - entry-model break-even percentage
illustrative entry ROI = expected payout for n independent, equally likely legs - 1
```

The ROI column is an illustration for an entire entry whose legs all have the displayed probability. It is **not** the return of one prop, a selected real lineup, or a guaranteed profit. Actual unequal-leg entries can be evaluated with `analysis.expected_return`, which assumes independence. This project does not estimate correlations, validate lineup eligibility, model leaderboard winnings, or account for DNPs/reboots/promotions.

Standard Player Picks minimum-guarantee payouts were checked against [PrizePicks Potential Outcomes](https://www.prizepicks.com/help-center/potential-outcomes) on October 19, 2026. Verify the actual payout shown in your account. The model excludes Team/Culture picks, Early Payout, discounted/Goblin/Demon projections, and leaderboard prizes.

## Reliability

- One HTTP response per collection trigger; clients poll explicit job state.
- In-process API lock plus a POSIX file lock for CLI/cron overlap.
- A failed collection preserves the last successful snapshot.
- Writes use a temporary file and atomic replacement.
- Versioned snapshots reject legacy/fake result formats.
- Expired observations and started games are hidden on every API read.
- Empty/unavailable data never falls back to fake bets.
- Browser adapters use normal Playwright Chromium with no stealth scripts, fake geolocation, or automated challenge interaction.
- The API has a ten-minute collection deadline. The standalone CLI has per-navigation/initial-response timeouts.

The browser parser supports known PrizePicks JSON projections and FanDuel event/market attachments. FanDuel navigation is bounded by `--max-events` and may not load all player markets or lazy-loaded tabs. Changed response schemas, blocked requests, missing player tabs, and inconsistent event times can result in no accepted matches. This is reported as a failure, not a fresh empty success.

## API

| Endpoint | Response |
| --- | --- |
| `GET /health` | Server health |
| `GET /api/opportunities` | Fresh comparisons, summary, snapshot timestamp, collection state |
| `GET /api/opportunities/:id` | Fresh row or 404 |
| `GET /api/stats` | Summary of currently eligible matches |
| `POST /api/trigger-scrape` | 202 accepted, 409 already running, or explicit failure |
| `GET /api/scrape-status` | `idle`, `running`, `succeeded`, `failed`, or `interrupted` |

## Verification

```bash
python3 -m unittest discover -s tests -v
node --test server/server.test.js
npm run build --prefix client
```

Python tests use synthetic fixtures explicitly constructed in the test files. They cover string odds, invalid prices, no-vig normalization, full Flex payout math, exact-market matching, ambiguity, stale timestamps, modified projections, and preservation of prior snapshots after failure. API tests exercise job locking, launch failure, expiry, missing rows, and cross-site trigger rejection. Passing these tests does not validate current live source compatibility.

## Files

- `collectors.py`: public browser collection and strict source parsers
- `analysis.py`: market normalization, no-vig calculation, payout models, comparison
- `daily_scraper.py`: locking, collection status, atomic snapshot publishing
- `server/server.js`: API and built React hosting
- `client/src/`: dashboard, filters, sorting, status and methodology
- `tests/`, `server/server.test.js`: deterministic verification
- `data/`: ignored runtime snapshots and diagnostics

The repository inherited tracked `node_modules/` directories. `.gitignore` now prevents newly untracked dependencies; removing already-tracked dependency trees is separate repository housekeeping. Install from package lockfiles for reproducibility.

## Next step for live data

Restore permitted source access and capture successful public responses, then validate the adapters against them. A licensed provider with verified PrizePicks **and** FanDuel player-prop coverage is an alternative; no provider subscription, coverage, or integration is assumed here.
