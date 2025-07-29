# scraper.py - v29 (Final PrizePicks Module)

import asyncio
import random
from playwright.async_api import async_playwright

APP_URL = "https://app.prizepicks.com/"
PROJECTIONS_URL_PART = "api.prizepicks.com/projections"

async def main():
    """
    Definitive scraper version with a multi-method approach to handle pop-ups.
    This version is set to run headlessly (in the background).
    """
    print("Launching headless browser with manual stealth...")
    async with async_playwright() as p:
        # Set to headless=True for automated background operation.
        browser = await p.chromium.launch(headless=True) 
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
                    print(f"\n--- Intercepted Projections API Call! ---")
                    try:
                        projections_data = await response.json()
                        print("Successfully captured projections data.")
                    except Exception as e:
                        print(f"Error decoding JSON from response: {e}")

        page.on("response", handle_response)

        print(f"Navigating to {APP_URL}...")
        try:
            await page.goto(APP_URL, wait_until="domcontentloaded", timeout=90000)
            print("Page loaded.")

            # --- Handle Cookie Banner First ---
            try:
                print("Looking for cookie banner...")
                cookie_button = page.locator("button:has-text('Accept All')")
                await cookie_button.click(timeout=5000)
                print("Accepted cookies. Waiting for banner to disappear...")
                await cookie_button.wait_for(state="hidden", timeout=5000)
                print("Cookie banner is hidden.")
            except Exception:
                print("Cookie banner not found or already handled.")
            
            # --- Multi-Method Pop-up Handling ---
            try:
                tutorial_popup = page.locator('[data-testid="modal-public-container"]')
                if await tutorial_popup.is_visible(timeout=5000):
                    print("Pop-up is visible. Attempting to close...")
                    try:
                        close_button = tutorial_popup.locator('[data-testid="CloseIcon"]')
                        await close_button.click(timeout=3000)
                        print("Clicked the 'X' button.")
                        await tutorial_popup.wait_for(state="hidden", timeout=5000)
                        print("Pop-up is hidden after click.")
                    except Exception:
                        print("Could not click 'X' button. Trying 'Escape' key as a fallback...")
                        await page.keyboard.press("Escape")
                        await tutorial_popup.wait_for(state="hidden", timeout=5000)
                        print("Pop-up is hidden after Escape.")
                else:
                    print("No tutorial pop-up was visible.")
            except Exception:
                print("No tutorial pop-up found or it timed out.")


            # --- Best CAPTCHA Handling Logic ---
            captcha_attempts = 0
            max_attempts = 4
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
                        print(f"Holding mouse down for {hold_duration:.2f} seconds...")
                        await asyncio.sleep(hold_duration)
                        
                        await page.mouse.up()
                        print("Mouse released.")
                        await page.wait_for_timeout(3000)
                    
                    captcha_attempts += 1
                except Exception:
                    print("CAPTCHA not visible. Assuming it's solved or was never there.")
                    break
            else:
                print("Failed to solve CAPTCHA after all attempts.")


            # --- Dynamic Waiting Logic ---
            print("Waiting for API data to be captured...")
            start_time = asyncio.get_event_loop().time()
            while projections_data is None:
                if (asyncio.get_event_loop().time() - start_time) > 20:
                    print("Timed out waiting for projections data.")
                    break
                await page.wait_for_timeout(100)

        except Exception as e:
            print(f"An error occurred during navigation or interaction: {e}")
        
        await browser.close()
        print("Browser closed.")

        if projections_data:
            print("\n--- PrizePicks Scraper Complete! ---")
            players = {}
            for item in projections_data.get('included', []):
                if item['type'] == 'new_player':
                    player_id = item['id']
                    player_name = item['attributes']['display_name']
                    players[player_id] = player_name

            print(f"\nFound {len(players)} players. Now processing projections...\n")
            print("--- Available Props ---")
            for projection in projections_data.get('data', []):
                if projection['type'] == 'projection':
                    attributes = projection['attributes']
                    relationships = projection['relationships']
                    player_id = relationships['new_player']['data']['id']
                    player_name = players.get(player_id, "Unknown Player")
                    line_score = attributes['line_score']
                    stat_type = attributes['stat_type']
                    print(f"- {player_name}: {line_score} {stat_type}")
            
            print("\n-------------------------\n")
            print("Next step: Scrape a sportsbook and compare the odds!")
        else:
            print("\n--- ERROR ---")
            print("Could not capture the projections data.")


if __name__ == "__main__":
    asyncio.run(main())
