# fanduel_scraper.py

import asyncio
import random
from playwright.async_api import async_playwright

FANDUEL_HOME_URL = "https://sportsbook.fanduel.com/"

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
        return []

    player_names = list(prizepicks_props_by_player.keys())
    print(f"Will search FanDuel for {len(player_names)} players.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Keep visible for debugging
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # We will only search for the first 5 players for this test run to confirm functionality.
        for i, player_name in enumerate(player_names[:5]):
            print(f"\n--- ({i+1}/5) Searching for player: {player_name} ---")
            try:
                # For each player, we start fresh by navigating to the homepage.
                print(f"Navigating to FanDuel homepage for new search...")
                await page.goto(FANDUEL_HOME_URL, wait_until="domcontentloaded", timeout=90000)
                print("FanDuel homepage has loaded.")

                # --- RESILIENT CAPTCHA HANDLING ---
                try:
                    captcha_frame_locator = page.frame_locator("iframe[title*='Challenge']")
                    hold_button = captcha_frame_locator.locator("button:has-text('Press & Hold')")
                    await hold_button.wait_for(state="visible", timeout=7000)
                    
                    print(f"FanDuel CAPTCHA found! Attempting to solve...")
                    box = await hold_button.bounding_box()
                    if box:
                        await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        await page.mouse.down()
                        hold_duration = random.uniform(4.5, 6.5)
                        await asyncio.sleep(hold_duration)
                        await page.mouse.up()
                        print("Mouse released.")
                    await hold_button.wait_for(state="hidden", timeout=10000)
                    print("FanDuel CAPTCHA solved.")
                except Exception:
                    print("FanDuel CAPTCHA not visible or already handled.")

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
                
                # --- PARSING LOGIC ---
                print("Parsing loaded props...")
                market_groups = await page.locator(f'div[aria-label*="{player_name}"]').all()
                for group in market_groups:
                    category_title = await group.get_attribute("aria-label")
                    print(f"  Category: {category_title}")
                    
                    bet_rows = await group.locator('div[role="listitem"]').all()
                    for row in bet_rows:
                        prop_name = await row.locator('span').first.inner_text()
                        prop_odds = await row.locator('span').nth(1).inner_text()
                        print(f"    - Prop: {prop_name}, Odds: {prop_odds}")

            except Exception as e:
                print(f"A critical error occurred while searching for {player_name}: {e}")
                continue

        await browser.close()
        print("FanDuel browser closed.")
    
    return []
