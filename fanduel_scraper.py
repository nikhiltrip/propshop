# fanduel_scraper.py

import asyncio
import random
from playwright.async_api import async_playwright

FANDUEL_HOME_URL = "https://sportsbook.fanduel.com/"

# Add delays between players to appear more human
MIN_DELAY_BETWEEN_PLAYERS = 8  # seconds
MAX_DELAY_BETWEEN_PLAYERS = 15  # seconds

async def solve_captcha(page, max_attempts=3):
    """
    Attempts to solve FanDuel CAPTCHA with retry logic.
    Returns True if solved or not present, False if failed after all attempts.
    """
    for attempt in range(max_attempts):
        try:
            captcha_frame_locator = page.frame_locator("iframe[title*='Challenge']")
            hold_button = captcha_frame_locator.locator("button:has-text('Press & Hold')")
            await hold_button.wait_for(state="visible", timeout=5000)
            
            print(f"  🔒 FanDuel CAPTCHA detected! Solving attempt {attempt + 1}/{max_attempts}...")
            box = await hold_button.bounding_box()
            if box:
                # Add slight random offset to make it more human-like
                offset_x = random.uniform(-5, 5)
                offset_y = random.uniform(-5, 5)
                await page.mouse.move(
                    box['x'] + box['width'] / 2 + offset_x, 
                    box['y'] + box['height'] / 2 + offset_y,
                    steps=random.randint(5, 15)
                )
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.mouse.down()
                
                # Longer and more variable hold duration
                hold_duration = random.uniform(6.0, 8.5)
                print(f"  ⏱️  Holding for {hold_duration:.1f} seconds...")
                await asyncio.sleep(hold_duration)
                await page.mouse.up()
                print("  ✓ Mouse released.")
            
            # Wait for CAPTCHA to disappear
            await hold_button.wait_for(state="hidden", timeout=12000)
            print("  ✓ CAPTCHA solved successfully!")
            return True
            
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"  ⚠️  CAPTCHA solve attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(random.uniform(1.0, 2.0))
            else:
                print("  ❌ CAPTCHA not visible or already solved.")
                return True  # Assume it's not there
    
    return False

async def fetch_odds(prizepicks_props_by_player: dict):
    """
    Scrapes FanDuel by searching for each player and then parsing the loaded props.
    This version uses the aria-label selector for maximum reliability.
    
    Args:
        prizepicks_props_by_player: A dict of props from PrizePicks, keyed by player name.
    """
    print("\n--- Running FanDuel Scraper (Aria-Label Strategy) ---")
    
    if not prizepicks_props_by_player:
        print("No PrizePicks props to compare against. Skipping FanDuel scrape.")
        return {}

    player_names = list(prizepicks_props_by_player.keys())
    print(f"Will search FanDuel for {len(player_names)} players.")
    
    # Store all scraped data
    all_fanduel_data = {}

    async with async_playwright() as p:
        # Better anti-detection for FanDuel
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            locale='en-US',
        )
        
        page = await context.new_page()
        
        # Enhanced stealth
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = {runtime: {}};
        """)

        # We will only search for the first 2 players for faster testing.
        for i, player_name in enumerate(player_names[:2]):
            print(f"\n--- ({i+1}/2) Searching for player: {player_name} ---")
            try:
                # For each player, we start fresh by navigating to the homepage.
                print(f"Navigating to FanDuel homepage for new search...")
                await page.goto(FANDUEL_HOME_URL, wait_until="domcontentloaded", timeout=90000)
                print("FanDuel homepage has loaded.")

                # --- IMPROVED CAPTCHA HANDLING ---
                captcha_solved = await solve_captcha(page)
                if not captcha_solved:
                    print("⚠️  Failed to solve CAPTCHA, skipping this player...")
                    continue

                # Patiently wait for the page to be interactive.
                print("Waiting for the page to become fully interactive...")
                search_icon_button = page.get_by_role("link", name="Search").first
                await search_icon_button.wait_for(state="visible", timeout=60000)
                print("Page is interactive. The search icon is now visible and ready.")

                await search_icon_button.click()
                print("Search icon clicked. Waiting for the search input field...")

                search_input = page.get_by_placeholder("Search")
                await search_input.wait_for(state="visible", timeout=15000)
                
                print("Typing the player's name into the search bar...")
                await search_input.fill(player_name, timeout=10000)
                
                # Wait for the prop markets to load
                print("Waiting for player prop markets to load on the search page...")
                market_container_selector = f'div[aria-label*="{player_name}"]'
                await page.locator(market_container_selector).first.wait_for(state="visible", timeout=15000)
                print("Player prop markets have loaded successfully.")
                
                # --- PARSING LOGIC WITH DATA STORAGE ---
                print("Parsing loaded props...")
                market_groups = await page.locator(f'div[aria-label*="{player_name}"]').all()
                
                # Get PrizePicks props for this player to match against
                prizepicks_props = prizepicks_props_by_player.get(player_name, [])
                
                # Store props temporarily to match Over/Under pairs
                temp_props = {}
                
                for group in market_groups:
                    aria_label = await group.get_attribute("aria-label")
                    if not aria_label:
                        continue
                    
                    # Parse aria-label format: "Player - Stat, Player Over/Under, Line, Odds"
                    # Example: "Deni Avdija - Points, Deni Avdija Over, 28.5, -136"
                    parts = [p.strip() for p in aria_label.split(",")]
                    
                    if len(parts) < 4:
                        continue  # Not a valid prop format
                    
                    # Extract components
                    stat_part = parts[0]  # "Deni Avdija - Points"
                    direction_part = parts[1]  # "Deni Avdija Over" or "Deni Avdija Under"
                    line_value = parts[2]  # "28.5"
                    odds_value = parts[3]  # "-136"
                    
                    # Extract stat type
                    if " - " not in stat_part:
                        continue
                    stat_type = stat_part.split(" - ")[1].strip()
                    
                    # Determine direction
                    if "Over" in direction_part:
                        direction = "Over"
                    elif "Under" in direction_part:
                        direction = "Under"
                    else:
                        continue
                    
                    # Check if this stat/line matches any PrizePicks prop for this player
                    matches_prizepicks = False
                    for pp_prop in prizepicks_props:
                        # Normalize stat names for comparison
                        pp_stat = pp_prop['stat'].lower()
                        fd_stat = stat_type.lower()
                        pp_line = str(pp_prop['line'])
                        
                        # Match stat type (handle variations like "Points" vs "Pts")
                        stat_match = (
                            pp_stat == fd_stat or
                            pp_stat in fd_stat or
                            fd_stat in pp_stat or
                            (pp_stat == "points" and "point" in fd_stat) or
                            (pp_stat == "rebounds" and "rebound" in fd_stat) or
                            (pp_stat == "assists" and "assist" in fd_stat)
                        )
                        
                        if stat_match and pp_line == line_value:
                            matches_prizepicks = True
                            break
                    
                    if not matches_prizepicks:
                        continue  # Skip props that don't match PrizePicks
                    
                    # Create unique key for this prop
                    prop_key = f"{player_name}|{stat_type}|{line_value}"
                    
                    if prop_key not in temp_props:
                        temp_props[prop_key] = {
                            "player": player_name,
                            "stat_type": stat_type,
                            "line": line_value,
                            "over_odds": None,
                            "under_odds": None
                        }
                    
                    # Add the odds
                    if direction == "Over":
                        temp_props[prop_key]["over_odds"] = odds_value
                    else:
                        temp_props[prop_key]["under_odds"] = odds_value
                
                # Convert temp props to final list and output
                player_props = []
                for prop_key, prop_data in temp_props.items():
                    if prop_data["over_odds"] and prop_data["under_odds"]:
                        player_props.append(prop_data)
                        print(f"  ✅ {prop_data['player']} - {prop_data['stat_type']} {prop_data['line']}, Over: {prop_data['over_odds']}, Under: {prop_data['under_odds']}")
                
                if not player_props:
                    print(f"  ⚠️  No matching FanDuel odds found for PrizePicks lines")
                
                
                if player_props:
                    all_fanduel_data[player_name] = player_props
                    print(f"  ✅ Captured {len(player_props)} props for {player_name}")
                else:
                    print(f"  ⚠️  No relevant props found for {player_name}")

            except Exception as e:
                print(f"A critical error occurred while searching for {player_name}: {e}")
                continue
            
            # Add human-like delay between players
            if i < 1:  # Don't delay after last player
                delay = random.uniform(MIN_DELAY_BETWEEN_PLAYERS, MAX_DELAY_BETWEEN_PLAYERS)
                print(f"\n⏱️  Waiting {delay:.1f}s before next player (appears more human)...")
                await asyncio.sleep(delay)

        await browser.close()
        print("\n✅ FanDuel browser closed.")
    
    print(f"\n📦 Successfully scraped FanDuel data for {len(all_fanduel_data)} players")
    return all_fanduel_data
