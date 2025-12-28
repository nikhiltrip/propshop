# PropShop - Sports Betting Edge Analyzer

A full-stack web application that identifies positive expected value (+EV) betting opportunities by analyzing PrizePicks prop lines against FanDuel market odds. The system uses automated daily scraping, statistical analysis, and an interactive dashboard to surface profitable betting edges.

## Overview

PropShop compares PrizePicks projections with FanDuel's no-vig probabilities to identify bets where your expected win rate exceeds the minimum threshold for profitability. The application features a modern React dashboard with real-time filtering, search capabilities, and manual line adjustment tools.

## Architecture

The system uses a batch processing architecture that runs once daily at midnight PST:

- **Daily Scraper**: Automated Python script that collects data from PrizePicks and FanDuel
- **File Storage**: Results stored in JSON format for instant dashboard access
- **Node.js Backend**: Express server that serves pre-computed opportunities
- **React Frontend**: Interactive dashboard with filtering, search, and manual editing features
- **Cron Automation**: Scheduled midnight runs with manual override capability

Data is not live - the dashboard displays opportunities from the most recent daily scrape. This design prioritizes instant page loads and minimizes API costs over real-time updates.

## Key Features

### Data Collection
- Automated web scraping using Playwright browser automation
- Collects PrizePicks projections and FanDuel market odds
- Processes 400+ player props across NBA, NFL, MLB, and NHL
- Calculates no-vig probabilities to remove bookmaker margin
- Identifies qualifying bet types based on edge thresholds

### Dashboard Interface
- Sport-specific filtering (NBA, NFL, MLB, NHL)
- Player name search with live filtering
- Sortable columns (edge, player, line)
- Edge-based filtering with adjustable threshold slider
- Manual line editing with real-time edge recalculation
- Data freshness indicators and stale data warnings
- Color-coded sport badges and edge indicators

### Analysis Engine
- Calculates true win probabilities from FanDuel odds
- Compares against PrizePicks bet type thresholds
- Identifies optimal betting strategies (2-6 pick parlays)
- Computes expected edge for each opportunity
- Supports both Power Play and Flex Play bet types

### Automation
- Cron job scheduled for midnight PST daily runs
- Manual trigger endpoint for on-demand updates
- Graceful error handling with detailed logging
- Automatic data persistence between runs
- Manual override when automation fails

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn package manager

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd propshop
   ```

2. Install Python dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install playwright asyncio fastapi uvicorn
   playwright install chromium
   ```

3. Install Node.js dependencies:
   ```bash
   cd server
   npm install
   cd ../client
   npm install
   cd ..
   ```

4. Set up the automated cron job:
   ```bash
   ./setup_cron.sh
   ```

## Usage

### Starting the Dashboard

Terminal 1 - Start the Node.js backend:
```bash
cd server
npm start
```

Terminal 2 - Start the React frontend:
```bash
cd client
npm start
```

The dashboard will be available at `http://localhost:3000`

### Manual Data Collection

To manually run the scraper and update data:
```bash
python daily_scraper.py
```

This will overwrite the existing data file with fresh opportunities. Use this when the automated cron job fails or when you want to update data outside the scheduled time.

### Command Line Analysis

For terminal-based analysis without the dashboard:
```bash
python main.py
```

## Project Structure

```
propshop/
├── daily_scraper.py           # Automated batch scraper
├── main.py                    # CLI tool and FastAPI server (deprecated)
├── prizepicks_scraper.py      # PrizePicks data collection
├── fanduel_scraper.py         # FanDuel odds scraping
├── setup_cron.sh              # Cron job installation script
├── server/
│   └── server.js              # Express API server
├── client/
│   ├── src/
│   │   ├── App.js             # Main React component
│   │   ├── components/
│   │   │   ├── OpportunityTable.js
│   │   │   └── StatsCard.js
│   │   └── App.css
│   └── package.json
└── data/
    └── opportunities.json      # Scraped opportunities (gitignored)
```

## How It Works

### Data Collection Pipeline

1. **PrizePicks Scraper**: Intercepts API calls to capture projection data including player names, stats, and lines
2. **FanDuel Scraper**: Searches for corresponding players and extracts over/under odds for each prop
3. **Probability Calculation**: Removes bookmaker vig to calculate true no-vig probabilities
4. **Edge Analysis**: Compares win probabilities against PrizePicks bet type thresholds
5. **Opportunity Detection**: Identifies bets where expected edge exceeds zero
6. **Data Formatting**: Structures results with sport detection and bet recommendations
7. **File Storage**: Saves to JSON for instant dashboard access

### Bet Type Analysis

The system evaluates nine different PrizePicks bet structures:

**Power Play Bets** (all picks must hit):
- 2-Pick: 57.74% win rate needed, 3x payout
- 3-Pick: 55.05% win rate needed, 6x payout
- 4-Pick: 56.23% win rate needed, 10x payout
- 5-Pick: 54.93% win rate needed, 20x payout
- 6-Pick: 54.66% win rate needed, 37.5x payout

**Flex Play Bets** (allows one miss):
- 3-Pick: 57.74% win rate needed, 3x payout
- 4-Pick: 55.04% win rate needed, 6x payout
- 5-Pick: 54.26% win rate needed, 10x payout
- 6-Pick: 54.21% win rate needed, 25x payout

### Manual Line Adjustment

The dashboard allows manual line editing to account for market movements throughout the day. When you edit a line:

1. The system estimates the new win probability using a linear approximation
2. Each 1% line change affects win probability by approximately 2%
3. Edge is recalculated based on the adjusted probability
4. Changes are reflected immediately without re-scraping

This feature is approximate and intended for quick what-if analysis rather than precise calculations.

## Configuration

### Cron Job Schedule

By default, the scraper runs at midnight PST (8 AM UTC). To modify:

```bash
crontab -e
```

Adjust the time in the cron expression:
```
0 8 * * * cd /path/to/propshop && /path/to/venv/bin/python daily_scraper.py >> logs/scraper.log 2>&1
```

### Data Freshness

The dashboard displays a warning when data is more than 24 hours old. Lines can move significantly in that time, so stale data should be refreshed before making betting decisions.

## API Endpoints

The Node.js server exposes the following endpoints:

- `GET /api/opportunities` - Returns all +EV opportunities
- `GET /api/stats` - Returns aggregate statistics
- `POST /api/trigger-scrape` - Manually triggers the scraper
- `GET /health` - Server health check

## Technical Details

### Technologies Used

**Backend:**
- Python 3.12 with asyncio for concurrent scraping
- Playwright for browser automation
- Express.js for API server
- JSON file storage

**Frontend:**
- React 18.2.0 with hooks
- Axios for HTTP requests
- CSS3 with gradient styling
- Responsive design patterns

**Automation:**
- Unix cron for scheduling
- Bash scripts for setup
- Process spawning for manual triggers

### Browser Automation

Scrapers run in visible browser mode to handle CAPTCHAs and avoid bot detection. The system includes:

- User agent spoofing
- Navigator property overrides
- Cookie banner handling
- Geo-location simulation (California)
- Rate limiting with delays

### Data Format

Opportunities are stored in the following JSON structure:

```json
{
  "opportunities": [
    {
      "id": 1,
      "player": "Player Name",
      "sport": "NBA",
      "stat": "Points",
      "line": 25.5,
      "direction": "over",
      "odds": -120,
      "no_vig_win_pct": 55.5,
      "edge": 1.3,
      "best_bet_type": "6-Pick Flex",
      "payout": 25,
      "all_qualifying_bets": [...]
    }
  ],
  "stats": {
    "total_scanned": 398,
    "plus_ev_found": 30,
    "conversion_rate": 7.54,
    "avg_edge": 1.48,
    "best_edge": 4.36
  },
  "last_updated": "2025-12-27T00:15:23Z",
  "date": "2025-12-27"
}
```

## Known Limitations

### CAPTCHA Challenges

Betting sites actively prevent automated scraping using CAPTCHAs. The automated cron job may fail to complete, requiring manual intervention. When this happens, you can run the scraper manually and solve CAPTCHAs in the visible browser window.

### Processing Time

Scraping all 400+ players takes 15-25 minutes due to rate limiting and browser interactions. The batch processing architecture means you'll see yesterday's edges rather than live opportunities.

### Line Movement

Sports betting lines move constantly based on betting activity and news. Data from midnight may not reflect current market conditions. Use the manual line editing feature to adjust for known changes.

## Important Notes

**Legal Disclaimer**: This tool is for educational and analytical purposes only. Ensure sports betting is legal in your jurisdiction before use. The software does not place bets or handle money directly.

**Not Financial Advice**: Past edge does not guarantee future profits. Sports betting involves risk and this analysis does not account for all factors that affect outcomes.

**Rate Limiting**: Respect website terms of service. The scrapers include delays to avoid overwhelming servers.

**Geo-Restrictions**: PrizePicks and FanDuel have location restrictions. You may need to be in supported jurisdictions to access their sites.

## Future Enhancements

Potential improvements for production deployment:

- Integration with The Odds API for instant, CAPTCHA-free data access
- Database storage (PostgreSQL) for historical tracking
- Authentication system for multi-user access
- Bet tracking and performance analytics
- Mobile-responsive design improvements
- Push notifications for high-edge opportunities
- Bankroll management and Kelly Criterion integration

## Contributing

This project is maintained as a portfolio piece. Suggestions and improvements are welcome through pull requests or issues.

## License

This project is for personal and educational use. All rights reserved.

## Acknowledgments

Built with Playwright for web scraping, React for the frontend, and Express.js for the API layer. Inspired by sports analytics and advantage play communities.

---

**Risk Warning**: Sports betting involves financial risk. This tool provides analysis but does not guarantee profits. Always bet responsibly and within your means. Past performance does not indicate future results.
