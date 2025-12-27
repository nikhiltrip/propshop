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

    if not prizepicks_props_by_player or prizepicks_props_by_player is None:
        print("\n❌ Could not fetch props from PrizePicks (CAPTCHA failure or network error).")
        print("\n💡 SOLUTIONS:")
        print("   1. Try running again (CAPTCHAs appear randomly)")
        print("   2. Run during off-peak hours (2-6 AM EST)")
        print("   3. Consider using The Odds API (see CAPTCHA_SOLUTIONS.md)")
        print("\nExiting...")
        return

    print(f"\nSuccessfully fetched props for {len(prizepicks_props_by_player)} players from PrizePicks.")
    
    # Step 2: Fetch odds from FanDuel (async)
    fanduel_odds = await fetch_fanduel_odds(prizepicks_props_by_player)

    if not fanduel_odds:
        print("\n⚠️  Could not fetch odds from FanDuel. Comparison will be skipped.")
    else:
        print(f"\n✅ Successfully fetched odds for {len(fanduel_odds)} players from FanDuel.")
        
        # Show summary of what we collected
        print("\n📋 Data Collection Summary:")
        print(f"  - PrizePicks: {len(prizepicks_props_by_player)} players")
        print(f"  - FanDuel: {len(fanduel_odds)} players")
        
        # Find overlap
        common_players = set(prizepicks_props_by_player.keys()) & set(fanduel_odds.keys())
        print(f"  - Players with data from both sources: {len(common_players)}")
        if common_players:
            print(f"    Examples: {', '.join(list(common_players)[:3])}")


    # Step 3: (Future) Compare the data and find value
    print("\n--- Comparison Logic (Not Yet Implemented) ---")
    print("Next steps:")
    print("  1. Parse and normalize prop data from both sources")
    print("  2. Match equivalent props (e.g., 'Points Over 20.5' on both platforms)")
    print("  3. Calculate implied probability from FanDuel odds")
    print("  4. Compare against PrizePicks lines to find +EV opportunities")
    print("  5. Recommend betting strategies based on edge strength")

    
    print("\n--- Value Finder Finished ---")


if __name__ == "__main__":
    asyncio.run(main())