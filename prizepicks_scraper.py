# prizepicks_scraper.py

import asyncio
import random
from playwright.async_api import async_playwright
from pathlib import Path

APP_URL = "https://app.prizepicks.com/"
PROJECTIONS_URL_PART = "api.prizepicks.com/projections"

# Store browser data to maintain sessions and reduce CAPTCHA triggers
USER_DATA_DIR = Path.home() / ".propshop" / "browser_data"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

async def fetch_props():
    """
    Launches a visible browser to reliably scrape props from PrizePicks.
    Returns a dictionary of props, structured by player name.
    """
    print("Launching browser to fetch PrizePicks data (visible for reliability)...")
    async with async_playwright() as p:
        # Launch with better anti-detection
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        ) 
        
        # Use persistent context to save cookies/sessions
        context = await browser.new_context(
            permissions=["geolocation"],
            geolocation={"latitude": 34.0522, "longitude": -118.2437},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            locale='en-US',
            timezone_id='America/Los_Angeles',
        )
        
        page = await context.new_page()
        
        # Better anti-detection scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
        """)

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

            # --- ULTRA-IMPROVED CAPTCHA HANDLING ---
            captcha_attempts = 0
            max_attempts = 3
            while captcha_attempts < max_attempts:
                try:
                    captcha_frame_locator = page.frame_locator("iframe[title='Human Challenge']")
                    hold_button = captcha_frame_locator.locator("button:has-text('Press & Hold')")
                    await hold_button.wait_for(state="visible", timeout=7000)
                    
                    print("\n" + "="*60)
                    print(f"🔒 CAPTCHA DETECTED! Attempt {captcha_attempts + 1}/{max_attempts}")
                    print("="*60)
                    print("📋 INSTRUCTIONS:")
                    print("   1. Click and HOLD the button for 10-12 seconds")
                    print("   2. Do NOT release until the checkmark appears")
                    print("   3. Keep holding even if it seems long")
                    print("="*60 + "\n")
                    
                    box = await hold_button.bounding_box()
                    if box:
                        # Very human-like approach
                        offset_x = random.uniform(-15, 15)
                        offset_y = random.uniform(-15, 15)
                        
                        # Move slowly to button
                        await page.mouse.move(
                            box['x'] + box['width'] / 2 + offset_x,
                            box['y'] + box['height'] / 2 + offset_y,
                            steps=random.randint(20, 35)
                        )
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                        
                        # Press down
                        await page.mouse.down()
                        
                        # MUCH longer hold duration - this seems to be the issue
                        hold_duration = random.uniform(10.0, 15.0)
                        print(f"⏱️  Holding button for {hold_duration:.1f} seconds...")
                        print("   (This is normal - PrizePicks requires long holds)")
                        
                        # Hold with periodic updates
                        for i in range(int(hold_duration)):
                            await asyncio.sleep(1)
                            if i % 3 == 0:
                                print(f"   ...still holding ({i+1}/{int(hold_duration)}s)")
                        
                        await asyncio.sleep(hold_duration - int(hold_duration))  # Remaining fraction
                        await page.mouse.up()
                        print("✓ Mouse released, waiting for verification...")
                    
                    # Give MUCH more time to verify
                    await asyncio.sleep(5)
                    
                    # Check if CAPTCHA is gone
                    try:
                        await hold_button.wait_for(state="hidden", timeout=8000)
                        print("\n✅ CAPTCHA SOLVED SUCCESSFULLY!\n")
                        break
                    except:
                        captcha_attempts += 1
                        if captcha_attempts < max_attempts:
                            print("\n⚠️  CAPTCHA verification failed, retrying...\n")
                            await asyncio.sleep(3)
                        
                except Exception:
                    print("❌ CAPTCHA not visible or already solved.")
                    break
            else:
                print("\n" + "="*60)
                print("❌ CAPTCHA FAILED AFTER ALL ATTEMPTS")
                print("="*60)
                print("⚠️  PrizePicks CAPTCHA is very strict.")
                print("💡 TIP: Try using The Odds API instead (see CAPTCHA_SOLUTIONS.md)")
                print("="*60 + "\n")
                await browser.close()
                return None


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
