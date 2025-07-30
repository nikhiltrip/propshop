# prizepicks_scraper.py

import asyncio
import random
from playwright.async_api import async_playwright

APP_URL = "https://app.prizepicks.com/"
PROJECTIONS_URL_PART = "api.prizepicks.com/projections"

async def fetch_props():
    """
    Launches a visible browser to reliably scrape props from PrizePicks.
    Returns a dictionary of props, structured by player name.
    """
    print("Launching browser to fetch PrizePicks data (visible for reliability)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context(
            permissions=["geolocation"],
            geolocation={"latitude": 34.0522, "longitude": -118.2437},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        projections_data = None

        async def handle_response(response):
            nonlocal projections_data
            if PROJECTIONS_URL_PART in response.url and response.request.method == 'GET':
                if projections_data is None:
                    print("--- Intercepted PrizePicks API Call! ---")
                    try:
                        projections_data = await response.json()
                        print("Successfully captured PrizePicks data.")
                    except Exception as e:
                        print(f"Error decoding PrizePicks JSON: {e}")

        page.on("response", handle_response)

        print(f"Navigating to {APP_URL}...")
        try:
            await page.goto(APP_URL, wait_until="domcontentloaded", timeout=90000)
            print("Page loaded.")
            
            print("Waiting for page to settle...")
            await page.wait_for_timeout(3000)

            # --- More Robust Pop-up Handling ---
            try:
                cookie_button = page.locator("button:has-text('Accept All')")
                await cookie_button.click(timeout=5000)
                await cookie_button.wait_for(state="hidden", timeout=5000)
                print("Handled cookie banner.")
            except Exception:
                pass 

            try:
                tutorial_popup = page.locator('[data-testid="modal-public-container"]')
                if await tutorial_popup.is_visible(timeout=5000):
                    await page.keyboard.press("Escape")
                    await tutorial_popup.wait_for(state="hidden", timeout=5000)
                    print("Handled tutorial pop-up.")
            except Exception:
                pass

            # --- RESILIENT CAPTCHA HANDLING ---
            captcha_attempts = 0
            max_attempts = 5
            while captcha_attempts < max_attempts:
                try:
                    captcha_frame_locator = page.frame_locator("iframe[title='Human Challenge']")
                    hold_button = captcha_frame_locator.locator("button:has-text('Press & Hold')")
                    await hold_button.wait_for(state="visible", timeout=7000)
                    
                    print(f"CAPTCHA found! Attempting to solve (Attempt {captcha_attempts + 1}/{max_attempts})...")
                    box = await hold_button.bounding_box()
                    if box:
                        await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        await page.mouse.down()
                        hold_duration = random.uniform(4.5, 6.5)
                        await asyncio.sleep(hold_duration)
                        await page.mouse.up()
                        print("Mouse released.")
                    await page.wait_for_timeout(2000)
                    captcha_attempts += 1
                except Exception:
                    print("CAPTCHA not visible. Assuming it is solved.")
                    break
            else:
                 print("Failed to solve CAPTCHA after all attempts.")


            # --- Dynamic Waiting for Data ---
            print("Waiting for data to be captured...")
            start_time = asyncio.get_event_loop().time()
            while projections_data is None and (asyncio.get_event_loop().time() - start_time) <= 20:
                await page.wait_for_timeout(100)

        except Exception as e:
            print(f"An error occurred during PrizePicks scraping: {e}")
        
        await browser.close()
        print("PrizePicks browser closed.")

        if not projections_data:
            print("Could not retrieve data from PrizePicks.")
            return {}

        players = {item['id']: item['attributes']['display_name'] for item in projections_data.get('included', []) if item['type'] == 'new_player'}
        
        props_by_player = {}
        for projection in projections_data.get('data', []):
            if projection['type'] == 'projection':
                player_id = projection['relationships']['new_player']['data']['id']
                player_name = players.get(player_id)
                if player_name:
                    if player_name not in props_by_player:
                        props_by_player[player_name] = []
                    
                    props_by_player[player_name].append({
                        'stat': projection['attributes']['stat_type'],
                        'line': projection['attributes']['line_score']
                    })
        
        return props_by_player
