# PropShop Production Roadmap

## 🐛 Current Issues

1. **Multiple windows opening** - Each API call triggers fresh browser launches
2. **Manual CAPTCHA handling** - Requires human intervention every scrape
3. **Not headless** - Visible browsers required for CAPTCHA solving
4. **Slow (2-3 min per run)** - User waits while scrapers run
5. **Not scalable** - Can't run autonomously

## ✅ Immediate Fix (Implemented)

**Scrape Lock & Extended Cache**
- Prevents multiple simultaneous scrapes
- 30-minute cache instead of 5 minutes
- Returns "scraping in progress" if another user triggers scrape
- Reduces window spam

**Restart your Node server to apply:**
```bash
cd server
npm start
```

---

## 🎯 Long-Term Solutions

### **Solution 1: The Odds API** ⭐ RECOMMENDED
**Best for:** Production deployment, professional portfolios  
**Cost:** Free tier: 500 requests/month | Pro: $0.20-0.50 per 1000 requests  
**Time to implement:** 2-4 hours  
**Resume value:** ⭐⭐⭐⭐⭐

**What it does:**
- Replaces web scraping entirely
- Real-time odds from 40+ bookmakers (including FanDuel, DraftKings, etc.)
- No CAPTCHAs, no browsers, fully headless
- Legal and compliant with betting sites
- Historical data available

**API Example:**
```python
import requests

API_KEY = 'your_api_key'
SPORT = 'basketball_nba'
BOOKMAKERS = 'fanduel,draftkings,prizepicks'

response = requests.get(
    f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
    params={
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h,spreads,totals,player_props',
        'bookmakers': BOOKMAKERS
    }
)
```

**Implementation Steps:**
1. Sign up at https://the-odds-api.com/
2. Replace `prizepicks_scraper.py` and `fanduel_scraper.py` with API calls
3. Keep your analysis engine (`find_plus_ev_opportunities`)
4. Response time: < 1 second (vs 2-3 minutes)

**Pros:**
- ✅ No CAPTCHAs ever
- ✅ Fully headless/automated
- ✅ Fast (< 1 sec)
- ✅ Professional solution
- ✅ Great for resume ("integrated 3rd-party sports betting API")

**Cons:**
- ❌ Costs money after free tier
- ❌ May not have PrizePicks (but has DraftKings, FanDuel, etc.)

---

### **Solution 2: Scheduled Cron Job + Database**
**Best for:** Autonomous operation, production architecture  
**Cost:** Free (just hosting)  
**Time to implement:** 4-6 hours  
**Resume value:** ⭐⭐⭐⭐⭐

**What it does:**
- Scrapers run automatically every 30-60 minutes via cron
- Store results in SQLite/PostgreSQL/JSON file
- Dashboard reads from database only
- Users never trigger scrapes directly
- Scraping happens in background

**Architecture:**
```
Cron Job (every 30 min) → Python Scrapers → Database
                                              ↓
Dashboard (instant) ← Node.js API ← Database
```

**Implementation Steps:**
1. Add SQLite database or use JSON file storage
2. Modify Python to save results to DB instead of returning
3. Create background script: `scraper_daemon.py`
4. Set up cron job: `*/30 * * * * /path/to/venv/bin/python scraper_daemon.py`
5. Modify Node.js to read from DB instead of calling Python API

**Cron setup (crontab -e):**
```bash
# Run scrapers every 30 minutes
*/30 * * * * cd /Users/nikhiltripathi/propshop && /Users/nikhiltripathi/propshop/venv/bin/python scraper_daemon.py >> /tmp/propshop.log 2>&1
```

**Pros:**
- ✅ Users get instant results (< 50ms)
- ✅ Scraping runs automatically in background
- ✅ Shows production thinking (great for resume)
- ✅ Scalable to many users
- ✅ Free

**Cons:**
- ❌ Still need to solve CAPTCHA (see Solution 3 or 4)
- ❌ Data can be up to 30 minutes old

---

### **Solution 3: CAPTCHA Solving Service**
**Best for:** Automated scraping without changing scraping approach  
**Cost:** $1-3 per 1000 CAPTCHAs solved  
**Time to implement:** 3-5 hours  
**Resume value:** ⭐⭐⭐⭐

**What it does:**
- Intercepts CAPTCHA challenges
- Sends to service API (2Captcha, Anti-Captcha, CapMonster)
- Service solves it (human workers or AI)
- Returns solution in 10-30 seconds
- Fully automated, can run headless

**Popular Services:**
- **2Captcha**: $2.99 per 1000 reCAPTCHAs
- **Anti-Captcha**: $1.50 per 1000 reCAPTCHAs
- **CapMonster Cloud**: $0.80 per 1000 reCAPTCHAs

**Implementation Example (2Captcha):**
```python
from playwright.async_api import async_playwright
from twocaptcha import TwoCaptcha
import os

solver = TwoCaptcha(os.getenv('2CAPTCHA_API_KEY'))

async def solve_captcha_automated(page):
    # Get site key from page
    site_key = await page.evaluate('''
        document.querySelector('[data-sitekey]').getAttribute('data-sitekey')
    ''')
    
    # Send to 2Captcha
    result = solver.recaptcha(
        sitekey=site_key,
        url=page.url
    )
    
    # Apply solution
    await page.evaluate(f'''
        document.getElementById('g-recaptcha-response').innerHTML = '{result['code']}';
    ''')
    
    return True
```

**Integration Steps:**
1. Sign up for 2Captcha or similar
2. Replace manual CAPTCHA waits with API calls
3. Can now run headless: `browser.launch(headless=True)`
4. Fully automated

**Pros:**
- ✅ Fully automated (no human intervention)
- ✅ Can run headless
- ✅ Keep existing scraping logic
- ✅ Fast (10-30 sec per CAPTCHA)

**Cons:**
- ❌ Costs money per solve
- ❌ Still slower than API (Solution 1)
- ❌ May violate betting site ToS (gray area)

---

### **Solution 4: Residential Proxies + Enhanced Stealth**
**Best for:** Advanced scraping, avoiding CAPTCHAs altogether  
**Cost:** $5-50/month for proxy service  
**Time to implement:** 6-10 hours  
**Resume value:** ⭐⭐⭐⭐⭐

**What it does:**
- Rotate through residential IP addresses (look like real users)
- Enhanced browser fingerprinting evasion
- Slower request rates (human-like behavior)
- May still hit CAPTCHAs but far less frequently

**Proxy Services:**
- **Bright Data** (formerly Luminati): Industry leader, expensive
- **Smartproxy**: $12.5/GB, good for betting sites
- **Oxylabs**: $15/GB, residential proxies
- **IPRoyal**: $7/GB, cheaper alternative

**Implementation:**
```python
from playwright.async_api import async_playwright

proxy_config = {
    'server': 'http://proxy-server.com:8000',
    'username': 'your_username',
    'password': 'your_password'
}

async with async_playwright() as p:
    browser = await p.chromium.launch(
        headless=True,
        proxy=proxy_config
    )
    
    context = await browser.new_context(
        # Enhanced stealth
        locale='en-US',
        timezone_id='America/Los_Angeles',
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
        # Random canvas fingerprint
        extra_http_headers={
            'Accept-Language': 'en-US,en;q=0.9',
        }
    )
```

**Additional Stealth:**
1. Install `playwright-stealth` package
2. Randomize mouse movements
3. Add random typing delays
4. Vary time between requests (30-120 seconds)
5. Mimic real user behavior (scroll, hover, etc.)

**Pros:**
- ✅ Dramatically reduces CAPTCHAs
- ✅ Can run mostly automated
- ✅ Shows advanced scraping skills (great resume point)
- ✅ Scalable with proxy pools

**Cons:**
- ❌ Costs money monthly
- ❌ Still may hit CAPTCHAs occasionally
- ❌ Complex to implement properly
- ❌ May violate betting site ToS

---

## 📊 Solution Comparison Matrix

| Solution | Cost | Speed | Automation | Resume Value | Recommendation |
|----------|------|-------|------------|--------------|----------------|
| **The Odds API** | $0-199/mo | ⚡⚡⚡⚡⚡ (< 1s) | ✅ Full | ⭐⭐⭐⭐⭐ | **Best for production** |
| **Cron + DB** | Free | ⚡⚡⚡⚡ (50ms) | ✅ Full* | ⭐⭐⭐⭐⭐ | **Best for portfolio** |
| **CAPTCHA Service** | $1-3/1k | ⚡⚡⚡ (30s) | ✅ Full | ⭐⭐⭐⭐ | Good middle ground |
| **Proxies + Stealth** | $5-50/mo | ⚡⚡ (2-3min) | ⚡⚡⚡ Partial | ⭐⭐⭐⭐⭐ | For advanced users |

*Still needs CAPTCHA solution for background scraper

---

## 🚀 Recommended Implementation Path

### **Phase 1: Quick Wins (This Week)**
✅ Implemented scrape lock (prevents multiple windows)  
✅ Extended cache to 30 minutes  
⬜ Remove 2-player limit in fanduel_scraper.py  
⬜ Add loading message in dashboard during scrape  

### **Phase 2: Production Ready (Next 2 Weeks)**
**Option A - Free/Portfolio:**
1. Implement cron job + database storage
2. Integrate 2Captcha for automated solving ($3/month budget)
3. Dashboard reads from database
4. Add admin page to manually trigger scrape

**Option B - Paid/Professional:**
1. Sign up for The Odds API free tier
2. Replace scrapers with API calls
3. Keep analysis engine
4. Deploy to production

### **Phase 3: Scaling (Future)**
1. Add more bookmakers/props
2. Historical data tracking
3. Alert system (email when +EV found)
4. Mobile app
5. User accounts & betting history

---

## 💡 Interview Talking Points

**For your resume/interviews:**

1. **Started with web scraping** (Playwright, anti-detection)
2. **Identified scalability issues** (CAPTCHA, speed)
3. **Evaluated solutions** (API vs scraping vs hybrid)
4. **Implemented caching** (30-min cache, scrape locks)
5. **Migrated to API** (The Odds API integration)
6. **Production architecture** (cron jobs, database, caching)

**This shows:**
- Problem-solving evolution
- Cost-benefit analysis
- Production thinking
- Scalability awareness
- Multiple technology stacks

---

## 📝 Next Steps

1. **Decide on solution:** The Odds API vs Cron+CAPTCHA service
2. **Test current system:** Let cache work, see if 30 min is acceptable
3. **Remove player limit:** Scale to full dataset
4. **Commit changes:**
```bash
git add -A
git commit -m "Add scrape lock and extended cache (30 min) to prevent window spam"
git push
```

Want me to implement any specific solution?
