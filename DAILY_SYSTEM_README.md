# PropShop - Daily Analysis System

## 🎯 How It Works Now

PropShop has been redesigned for **once-daily scraping** instead of live updates:

1. **Automated scraper runs at midnight PST** (via cron job)
2. Results saved to `data/opportunities.json`
3. **Dashboard loads instantly** (< 50ms) - no scraping during the day
4. **Manual refresh button** if midnight scrape fails or you want fresh data

## 🚀 Quick Start

### 1. Test the scraper manually
```bash
/Users/nikhiltripathi/propshop/venv/bin/python daily_scraper.py
```

### 2. Start the dashboard
```bash
# Terminal 1 - Node.js server
cd server
npm start

# Terminal 2 - React frontend
cd client  
npm start
```

### 3. Set up automated midnight runs
```bash
./setup_cron.sh
```

## ✨ New Features

### Dashboard
- **Sport filtering** - Filter by NBA, NFL, MLB, NHL
- **Player search** - Search for specific players
- **Edge sorting** - Sort by highest edge (default)
- **Stale data warning** - Shows if data is > 24 hours old
- **Manual refresh button** - Trigger fresh scrape anytime
- **Data freshness indicator** - Shows "Last updated" timestamp

### Backend
- **JSON file storage** - No live Python API calls during day
- **Manual trigger endpoint** - `POST /api/trigger-scrape`
- **Graceful fallback** - Shows warning if no data available

## 📁 New Files

- **`daily_scraper.py`** - Standalone scraper that saves to JSON
- **`data/opportunities.json`** - Current day's data (gitignored)
- **`logs/scraper.log`** - Scraper logs (gitignored)
- **`setup_cron.sh`** - Easy cron job setup script

## 🎓 Why This Approach?

### Problems Solved
✅ No more multiple windows opening  
✅ No CAPTCHA handling during day  
✅ Dashboard loads instantly  
✅ Can still manually refresh if needed  
✅ Runs unattended overnight  

### Trade-offs
⚠️ Data can be up to 24 hours old  
⚠️ Lines may have moved since midnight  
⚠️ Still need to solve CAPTCHA for midnight run (or manually in morning)

## 🔧 Manual Refresh

If the midnight scrape fails (CAPTCHA), you can manually refresh:

**In Dashboard:**
- Click **"⚠️ Refresh Stale Data"** button
- Wait 2-3 minutes for scraping to complete
- Dashboard will auto-update when done

**Via Command Line:**
```bash
/Users/nikhiltripathi/propshop/venv/bin/python daily_scraper.py
```

**Via API:**
```bash
curl -X POST http://localhost:3001/api/trigger-scrape
```

## 📊 Data Format

`data/opportunities.json`:
```json
{
  "date": "2025-12-27",
  "last_updated": "2025-12-27T08:15:23Z",
  "opportunities": [
    {
      "id": 1,
      "player": "Luka Doncic",
      "sport": "NBA",
      "stat": "Points",
      "line": 32.5,
      "direction": "over",
      "odds": -125,
      "no_vig_win_pct": 55.81,
      "edge": 1.60,
      "best_bet_type": "6-Pick Flex",
      "payout": 25,
      "all_qualifying_bets": [...]
    }
  ],
  "stats": {
    "total_scanned": 150,
    "plus_ev_found": 12,
    "conversion_rate": 8.0,
    "avg_edge": 1.23,
    "best_edge": 3.45
  }
}
```

## 🕐 Cron Job Details

The scraper runs at **midnight PST** (8 AM UTC):
```bash
# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Remove all cron jobs
crontab -r
```

**Cron expression:**
```
0 8 * * * cd /path/to/propshop && /path/to/venv/bin/python daily_scraper.py >> logs/scraper.log 2>&1
```

## 🐛 Troubleshooting

**Dashboard shows "No data available":**
- Run: `/Users/nikhiltripathi/propshop/venv/bin/python daily_scraper.py`
- Or use the manual refresh button in dashboard

**Cron job not running:**
- Check logs: `tail -f logs/scraper.log`
- Verify cron: `crontab -l`
- Test manually first to ensure it works

**Data is stale:**
- Check if midnight scrape failed (CAPTCHA)
- Click "Refresh Stale Data" button
- Or run scraper manually

## 🎯 Next Steps (Optional Upgrades)

1. **CAPTCHA Service Integration** ($3/month)
   - Add 2Captcha or Anti-Captcha
   - Fully automated, no manual intervention
   - See: `PRODUCTION_ROADMAP.md`

2. **The Odds API** (Free tier available)
   - Replace scraping with API calls
   - No CAPTCHAs ever
   - < 1 second response time
   - See: `PRODUCTION_ROADMAP.md`

3. **Database Storage**
   - SQLite or PostgreSQL
   - Historical data tracking
   - Performance analytics

## 📝 Architecture

```
Cron Job (midnight)
    ↓
daily_scraper.py
    ↓
PrizePicks + FanDuel scrapers
    ↓
data/opportunities.json
    ↓
Node.js API (reads JSON)
    ↓
React Dashboard (instant load)
```

## 🎓 Resume Points

- **Automated data pipeline** with cron scheduling
- **Real-time vs. batch processing** design decisions
- **Graceful degradation** with fallback mechanisms
- **User experience optimization** (instant dashboard loads)
- **Cost-benefit analysis** (daily vs. live scraping)
- **Full-stack implementation** (Python + Node + React)
