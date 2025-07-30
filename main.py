# main.py

import asyncio
from prizepicks_scraper import fetch_props as fetch_prizepicks_props
from fanduel_scraper import fetch_odds as fetch_fanduel_odds

async def main():
    """
    Main function to run all scrapers and process the data.
    """
    print("--- Starting Value Finder ---")

    # Step 1: Fetch props from PrizePicks (async)
    prizepicks_props_by_player = await fetch_prizepicks_props()

    if not prizepicks_props_by_player:
        print("Could not fetch props from PrizePicks. Exiting.")
        return

    print(f"\nSuccessfully fetched props for {len(prizepicks_props_by_player)} players from PrizePicks.")
    
    # Step 2: Fetch odds from FanDuel (async)
    fanduel_odds = await fetch_fanduel_odds(prizepicks_props_by_player)


    if not fanduel_odds:
        print("\nCould not fetch odds from FanDuel. Comparison will be skipped.")
    else:
        print(f"\nSuccessfully fetched {len(fanduel_odds)} odds from FanDuel.")


    # Step 3: (Future) Compare the data and find value
    print("\n--- Comparison Logic (Not Yet Implemented) ---")

    
    print("\n--- Value Finder Finished ---")


if __name__ == "__main__":
    asyncio.run(main())