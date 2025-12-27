# PropShop - +EV Sports Betting Analyzer

> **WORK IN PROGRESS** -

A Python-based tool (in development) that will identify guaranteed positive expected value (+EV) betting opportunities by comparing PrizePicks prop lines with FanDuel odds. When specific threshold conditions are met, the tool will recommend optimal betting strategies to maximize long-term profit.

## Project Goal

Find guaranteed +EV bets by:
1. Scraping prop lines from PrizePicks
2. Comparing them to corresponding odds on FanDuel
3. Identifying opportunities where the mathematical edge guarantees profit over time
4. Recommending optimal betting strategies (e.g., 2-man power parlay, 4-man flex)

## Features

- **Automated Web Scraping**: Uses Playwright to reliably scrape data from both platforms
- **CAPTCHA Handling**: Built-in resilient CAPTCHA solving for both PrizePicks and FanDuel
- **Player-Based Analysis**: Organizes props by player for easy comparison
- **Geo-spoofing**: Simulates California location for PrizePicks access
- **Async Processing**: Fast, efficient data collection using Python's asyncio

## Prerequisites

- Python 3.8 or higher
- Internet connection
- Valid access to PrizePicks and FanDuel (must be in supported jurisdictions)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd propshop
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install playwright asyncio
   playwright install chromium
   ```

## Usagetest the scrapers:

```bash
python main.py
```

**Current functionality:**
1. Launches a browser window to scrape PrizePicks props
2. Searches FanDuel for corresponding player odds (first 5 players only)
3. Prints raw data to console

**Note:** The script currently only collects data. The comparison logic and +EV analysis are not yet implemented.
2. Search FanDuel for corresponding player odds
3. Display comparison data (comparison logic coming soon)

## Project Structure

```
propshop/
├── main.py                  # Main orchestration script
├── prizepicks_scraper.py    # PrizePicks data collection
├── fanduel_scraper.py       # FanDuel odds scraping
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## How It Works

### 1. PrizePicks Scraper
- Navigates to PrizePicks with a headless browser
- Intercepts API calls to capture raw projection data
- Handles authentication and CAPTCHA challenges
- Returns player props organized by player name

### 2. FanDuel Scraper
- Searches for each player from PrizePicks data
- Extracts corresponding**NOT YET IMPLEMENTED**)
Will identify +EV opportunities by:
- Calculating implied probability from FanDuel odds
- Comparing against PrizePicks lines
- Identifying threshold conditions that guarantee long-term profit
- Applying Kelly Criterion or similar bankroll management
- Recommending optimal parlay configurations based on edge strength
- Calculating implied probability from FanDuel odds
- Comparing against PrizePicks lines
- Applying Kelly Criterion or similar bankroll management
- Recommending optimal parlay configurations

## Betting Strategies (To Be Implemented)

The tool will recommend strategies based on edge strength:
- **2-Man Power Parlay**: High confidence, lower risk
- **3-Man Flex**: Balanced approach with insurance
- *Current Limitations

- **Incomplete**: Core comparison and analysis features are not implemented
- **Limited Scope**: Only processes first 5 players from PrizePicks
- **No Data Persistence**: Scraped data is only printed, not saved
- **No Error Recovery**: Script may fail if websites change their structure
- **Manual CAPTCHA**: May require manual intervention if CAPTCHA solving fails
- **Slow Execution**: Browser-based scraping takes several minutes to run

## Important Notes

- **Legal Disclaimer**: This tool is for educational and analytical purposes only. Ensure sports betting is legal in your jurisdiction before use.
- **Browser Visibility**: Browsers run in non-headless mode to avoid detection and handle CAPTCHAs
- **Rate Limiting**: The script includes delays to avoid overwhelming servers
- **Geo-Restrictions**: May require VPN or location spoofing based on your location
- **Early Stage**: Expect bugs, incomplete features, and frequent changesEnsure sports betting is legal in your jurisdiction before use.
- **Browser Visibility**: Browsers run in non-headless mode to avoid detection and handle CAPTCHAs
- **Rate Limiting**: The script includes delays to avoid overwhelming servers
- **Geo-Restrictions**: May require VPN or location spoofing based on your location
**Completed:**
- [x] Basic PrizePicks scraping (intercepts API calls)
- [x] Basic FanDuel scraping (search-based, limited to 5 players)
- [x] CAPTCHA handling for both platforms

**In Progress:**
- [ ] Data parsing and normalization
- [ ] Complete FanDuel scraping (all players)
- [ ] Store scraped data in structured format

**Not Started:**
- [ ] Odds comparison logic
- [ ] +EV calculation algorithm  
- [ ] Threshold detection for guaranteed profit
- [ ] Betting strategy recommendations
- [ ] Results logging and tracking
- [ ] Historical performance analysis
- [ ] Command-line interface with options
- [ ] Output formatting (CSV, JSON, etc.)
- [ ] Betting strategy recommendations
- [ ] Results logging and tracking
- [ ] Historical performance analysis

## Contributing

This is a personal project, but suggestions and improvements are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is for personal use. All rights reserved.

## Acknowledgments

- Built with [Playwright](https://playwright.dev/) for reliable web scraping
- Inspired by the sports analytics and advantage play community

---

**Disclaimer**: Sports betting involves risk. This tool provides analysis but does not guarantee profits. Always bet responsibly and within your means.
