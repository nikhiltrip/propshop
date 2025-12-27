# main.py

import asyncio
from prizepicks_scraper import fetch_props as fetch_prizepicks_props
from fanduel_scraper import fetch_odds as fetch_fanduel_odds

# PrizePicks payout structures and minimum win % thresholds
BET_TYPES = {
    "2-Pick Power": {"payout": 3, "min_win_pct": 57.74, "type": "power"},
    "3-Pick Power": {"payout": 6, "min_win_pct": 55.05, "type": "power"},
    "4-Pick Power": {"payout": 10, "min_win_pct": 56.23, "type": "power"},
    "5-Pick Power": {"payout": 20, "min_win_pct": 54.93, "type": "power"},
    "6-Pick Power": {"payout": 37.5, "min_win_pct": 54.66, "type": "power"},
    "3-Pick Flex": {"payout": 3, "min_win_pct": 57.74, "type": "flex"},
    "4-Pick Flex": {"payout": 6, "min_win_pct": 55.04, "type": "flex"},
    "5-Pick Flex": {"payout": 10, "min_win_pct": 54.26, "type": "flex"},
    "6-Pick Flex": {"payout": 25, "min_win_pct": 54.21, "type": "flex"},
}

def american_to_probability(odds):
    """Convert American odds to implied probability percentage."""
    if odds > 0:
        return 100 / (odds + 100) * 100
    else:
        return abs(odds) / (abs(odds) + 100) * 100

def calculate_no_vig_probability(over_odds, under_odds):
    """
    Calculate the true (no-vig) probability from FanDuel's Over/Under odds.
    Removes the bookmaker's vig to get fair market probability.
    """
    over_prob = american_to_probability(over_odds)
    under_prob = american_to_probability(under_odds)
    total_prob = over_prob + under_prob
    
    # Remove vig and normalize
    no_vig_over = (over_prob / total_prob) * 100
    no_vig_under = (under_prob / total_prob) * 100
    
    return no_vig_over, no_vig_under

def find_plus_ev_opportunities(fanduel_odds):
    """
    Analyze FanDuel odds to find +EV opportunities for PrizePicks.
    Returns a dict of player -> [{prop info, recommended bets}]
    """
    opportunities = {}
    
    for player, props in fanduel_odds.items():
        player_opps = []
        
        for prop in props:
            stat = prop['stat']
            line = prop['line']
            over_odds = prop['over_odds']
            under_odds = prop['under_odds']
            
            # Calculate no-vig probabilities
            no_vig_over, no_vig_under = calculate_no_vig_probability(over_odds, under_odds)
            
            # Check which bet types this prop qualifies for (Over)
            over_qualifies = []
            for bet_name, bet_info in BET_TYPES.items():
                if no_vig_over >= bet_info['min_win_pct']:
                    edge = no_vig_over - bet_info['min_win_pct']
                    over_qualifies.append({
                        'bet_type': bet_name,
                        'edge': edge,
                        'payout': bet_info['payout']
                    })
            
            # Check which bet types this prop qualifies for (Under)
            under_qualifies = []
            for bet_name, bet_info in BET_TYPES.items():
                if no_vig_under >= bet_info['min_win_pct']:
                    edge = no_vig_under - bet_info['min_win_pct']
                    under_qualifies.append({
                        'bet_type': bet_name,
                        'edge': edge,
                        'payout': bet_info['payout']
                    })
            
            if over_qualifies or under_qualifies:
                player_opps.append({
                    'stat': stat,
                    'line': line,
                    'over_odds': over_odds,
                    'under_odds': under_odds,
                    'no_vig_over': no_vig_over,
                    'no_vig_under': no_vig_under,
                    'over_qualifies': over_qualifies,
                    'under_qualifies': under_qualifies
                })
        
        if player_opps:
            opportunities[player] = player_opps
    
    return opportunities

def display_opportunities(opportunities):
    """Display +EV opportunities in a clear format."""
    if not opportunities:
        print("\n❌ No +EV opportunities found at this time.")
        print("   Try checking again later or adjusting your strategy.")
        return
    
    print("\n" + "="*80)
    print("💰 +EV OPPORTUNITIES FOUND")
    print("="*80)
    
    total_opps = sum(len(props) for props in opportunities.values())
    print(f"\nFound {total_opps} +EV props across {len(opportunities)} players\n")
    
    for player, props in sorted(opportunities.items()):
        print(f"\n🏀 {player}")
        print("-" * 80)
        
        for prop in props:
            stat = prop['stat']
            line = prop['line']
            
            print(f"\n   {stat} {line}")
            print(f"   FanDuel Odds: Over {prop['over_odds']:+d} | Under {prop['under_odds']:+d}")
            print(f"   No-Vig Win%: Over {prop['no_vig_over']:.2f}% | Under {prop['no_vig_under']:.2f}%")
            
            # Display Over recommendations
            if prop['over_qualifies']:
                print(f"\n   ✅ OVER Recommendations:")
                for qual in sorted(prop['over_qualifies'], key=lambda x: x['edge'], reverse=True):
                    print(f"      • {qual['bet_type']}: +{qual['edge']:.2f}% edge (pays {qual['payout']}x)")
            
            # Display Under recommendations
            if prop['under_qualifies']:
                print(f"\n   ✅ UNDER Recommendations:")
                for qual in sorted(prop['under_qualifies'], key=lambda x: x['edge'], reverse=True):
                    print(f"      • {qual['bet_type']}: +{qual['edge']:.2f}% edge (pays {qual['payout']}x)")
            
            print()

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


    # Step 3: Analyze for +EV opportunities
    if fanduel_odds:
        print("\n--- Analyzing for +EV Opportunities ---")
        opportunities = find_plus_ev_opportunities(fanduel_odds)
        display_opportunities(opportunities)
    
    print("\n" + "="*80)
    print("--- Value Finder Finished ---")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())