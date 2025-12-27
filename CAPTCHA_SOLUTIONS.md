# CAPTCHA Solutions & Anti-Detection Strategies

## Why CAPTCHAs Appear Randomly

Betting sites use sophisticated bot detection systems that analyze:

1. **Browser Fingerprinting** - Detects automation signals (Playwright, Selenium)
2. **IP Reputation** - Tracks request frequency from your IP
3. **Behavioral Patterns** - Mouse movements, typing speed, navigation patterns
4. **Session Data** - New sessions without cookies are suspicious
5. **Request Timing** - Too fast or too regular = bot

## Current Improvements (Already Implemented)

✅ **Better User Agent** - Using realistic Chrome on macOS
✅ **Enhanced Stealth Scripts** - Hiding `navigator.webdriver` and other automation flags
✅ **Realistic Browser Args** - Disabling automation control features
✅ **Human-like Delays** - Random waits between actions (8-15 seconds between players)
✅ **Improved CAPTCHA Handling** - Longer hold times (7-9.5s), random offsets, retry logic
✅ **Viewport Size** - Standard 1920x1080 resolution
✅ **Session Persistence** - Saves browser data to maintain cookies

## Additional Solutions to Try

### 1. **Residential Proxies** (Reduces CAPTCHAs by 80%+)
Use residential IPs that rotate to avoid IP-based detection:

**Recommended Services:**
- **Bright Data (Luminati)** - $500/month, best quality
- **Smartproxy** - $75/month for 5GB
- **Oxylabs** - Enterprise-level

```python
# Add to browser context:
proxy={
    "server": "http://proxy-server:port",
    "username": "user",
    "password": "pass"
}
```

### 2. **Playwright Extra with Stealth Plugin**
Install plugins that better hide automation:

```bash
pip install playwright-stealth
```

```python
from playwright_stealth import stealth_async

# After creating page:
await stealth_async(page)
```

### 3. **CAPTCHA Solving Services** (For Automated Headless Mode)
When you can't manually solve CAPTCHAs:

**Services:**
- **2Captcha** - ~$3 per 1000 solves
- **Anti-Captcha** - Similar pricing
- **CapSolver** - Specialized in click CAPTCHAs

**Integration:**
```python
# Send CAPTCHA image to service
# Get solution back
# Apply solution to form
```

### 4. **Browser Profiles & Cookie Management**
Reuse authenticated browser sessions:

```python
# Save cookies after first successful login
cookies = await context.cookies()
# Store in file

# Load on next run
await context.add_cookies(saved_cookies)
```

### 5. **Undetected ChromeDriver Alternative**
For Python Selenium users (not Playwright):

```bash
pip install undetected-chromedriver
```

## Third-Party APIs (Best Long-Term Solution)

### **PrizePicks Alternative: PropSwap API**
- **Issue:** PrizePicks has very aggressive CAPTCHA
- **Alternative:** PropSwap has similar prop data and may have API access
- **Reality Check:** Most DFS sites don't offer public APIs

### **The Odds API** ⭐ (Recommended for FanDuel)
- **Website:** https://the-odds-api.com/
- **Cost:** $70/month for 10,000 requests
- **Free Tier:** 100 requests/month (good for testing)
- **Coverage:** 40+ bookmakers including FanDuel
- **Pros:** No scraping, no CAPTCHAs, legal, reliable
- **Cons:** Doesn't have PrizePicks data

```python
import requests

response = requests.get(
    'https://api.the-odds-api.com/v4/sports/basketball_nba/odds',
    params={
        'apiKey': 'YOUR_KEY',
        'regions': 'us',
        'markets': 'player_points,player_rebounds',
        'bookmakers': 'fanduel'
    }
)
odds = response.json()
```

### **RapidOdds (Alternative)**
- **Website:** https://rapidapi.com/theoddsapi/api/live-sports-odds
- **Cost:** $10-30/month
- **Similar to The Odds API but different pricing structure**

## Recommended Approach

### **Phase 1: Current (Development)**
- ✅ Use improved scraping with better anti-detection
- ✅ Manually solve CAPTCHAs during testing
- ✅ Run during off-peak hours (less traffic = fewer CAPTCHAs)

### **Phase 2: Semi-Automated**
- Add residential proxy service ($75-100/month)
- Implement session persistence with cookies
- Run once per day at consistent times

### **Phase 3: Fully Automated (Production)**
- Use The Odds API for FanDuel data ($70/month)
- Keep scraping PrizePicks (lower CAPTCHA rate)
- OR: Use CAPTCHA solving service ($50-100/month)

### **Phase 4: Professional (Scale)**
- Full API integration for all sources
- No scraping, no CAPTCHAs, 99.9% uptime
- Focus on analysis algorithms instead of data collection

## Testing Tips

1. **Run at different times** - Late night has fewer CAPTCHAs
2. **Clear browser data occasionally** - Too many cookies can trigger flags
3. **Don't run too frequently** - Wait 30+ minutes between runs
4. **Use VPN/proxy** - Rotate IPs if running multiple times per day
5. **Keep browser visible** - Headless mode triggers more CAPTCHAs

## Cost Comparison

| Solution | Monthly Cost | CAPTCHA Reduction | Setup Complexity |
|----------|-------------|-------------------|------------------|
| Current (free) | $0 | 0% | ✅ Done |
| Residential Proxy | $75-100 | 80% | Medium |
| The Odds API | $70 | 100% (no scraping) | Easy |
| CAPTCHA Solver | $50-100 | 95% | Medium |
| Full API Stack | $200-500 | 100% | Easy |

## Immediate Next Steps

1. ✅ **Done:** Smaller browser windows (1280x800)
2. ✅ **Done:** Much longer CAPTCHA hold times (10-15 seconds)
3. ✅ **Done:** Better error handling and user guidance
4. **Recommended:** Sign up for The Odds API free tier (100 requests/month)
5. **Reality Check:** PrizePicks has very aggressive anti-bot measures
6. **Best Solution:** Hybrid approach:
   - Use The Odds API for FanDuel ($70/month or free tier)
   - Keep trying PrizePicks scraper (may need manual intervention)
   - OR: Manually export PrizePicks data as CSV for now

## If CAPTCHAs Keep Failing

**Option A: The Odds API (Recommended)**
- Sign up at https://the-odds-api.com/
- Get 100 free requests/month for testing
- Replace FanDuel scraper with API calls
- Keep PrizePicks scraper or manually input data

**Option B: Manual Hybrid**
- Run scrapers during low-traffic times (2-6 AM EST)
- Accept that some manual CAPTCHA solving is needed
- Run once per day maximum
- Use session persistence to reduce CAPTCHAs

**Option C: Wait & Retry**
- CAPTCHAs appear randomly based on many factors
- Sometimes a browser restart helps
- Clear cookies and try again
- Different times of day have different success rates
