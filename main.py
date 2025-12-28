# main.py

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from prizepicks_scraper import fetch_props as fetch_prizepicks_props
from fanduel_scraper import fetch_odds as fetch_fanduel_odds

# Initialize FastAPI app
app = FastAPI(
    title="PropShop +EV Analyzer",
    description="Real-time sports betting edge finder using PrizePicks and FanDuel data",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/analyze")
async def analyze_opportunities():
    """
    API endpoint that runs the full analysis pipeline:
    1. Fetches props from PrizePicks
    2. Fetches odds from FanDuel
    3. Analyzes for +EV opportunities
    4. Returns formatted JSON for the dashboard
    """
    try:
        # Fetch data from both sources
        prizepicks_props = await fetch_prizepicks_props()
        
        if not prizepicks_props:
            raise HTTPException(
                status_code=503,
                detail="Could not fetch PrizePicks data (CAPTCHA or network error)"
            )
        
        fanduel_odds = await fetch_fanduel_odds(prizepicks_props)
        
        if not fanduel_odds:
            raise HTTPException(
                status_code=503,
                detail="Could not fetch FanDuel odds"
            )
        
        # Analyze for +EV opportunities
        opportunities = find_plus_ev_opportunities(fanduel_odds)
        
        # Format for dashboard
        formatted_opps = []
        opp_id = 1
        
        for player, props in opportunities.items():
            for prop in props:
                # Determine best direction (Over or Under)
                best_over = max(prop['over_qualifies'], key=lambda x: x['edge']) if prop['over_qualifies'] else None
                best_under = max(prop['under_qualifies'], key=lambda x: x['edge']) if prop['under_qualifies'] else None
                
                if best_over and (not best_under or best_over['edge'] >= best_under['edge']):
                    direction = 'over'
                    best_bet = best_over
                    all_qualifies = prop['over_qualifies']
                    win_pct = prop['no_vig_over']
                else:
                    direction = 'under'
                    best_bet = best_under
                    all_qualifies = prop['under_qualifies']
                    win_pct = prop['no_vig_under']
                
                formatted_opps.append({
                    'id': opp_id,
                    'player': player,
                    'stat': prop['stat'],
                    'line': prop['line'],
                    'direction': direction,
                    'odds': prop['over_odds'] if direction == 'over' else prop['under_odds'],
                    'no_vig_win_pct': round(win_pct, 2),
                    'edge': round(best_bet['edge'], 2),
                    'best_bet_type': best_bet['bet_type'],
                    'payout': best_bet['payout'],
                    'all_qualifying_bets': [
                        {
                            'type': q['bet_type'],
                            'edge': round(q['edge'], 2),
                            'payout': q['payout']
                        } for q in sorted(all_qualifies, key=lambda x: x['edge'], reverse=True)
                    ]
                })
                opp_id += 1
        
        # Calculate stats
        total_props_scanned = sum(len(props) for props in fanduel_odds.values())
        total_plus_ev = len(formatted_opps)
        avg_edge = sum(opp['edge'] for opp in formatted_opps) / total_plus_ev if total_plus_ev > 0 else 0
        best_edge = max((opp['edge'] for opp in formatted_opps), default=0)
        
        return {
            'opportunities': formatted_opps,
            'stats': {
                'total_scanned': total_props_scanned,
                'plus_ev_found': total_plus_ev,
                'conversion_rate': round((total_plus_ev / total_props_scanned * 100), 2) if total_props_scanned > 0 else 0,
                'avg_edge': round(avg_edge, 2),
                'best_edge': round(best_edge, 2)
            },
            'timestamp': None  # Frontend will set this
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        'status': 'online',
        'service': 'PropShop +EV Analyzer',
        'endpoints': {
            '/api/analyze': 'Run full analysis pipeline',
            '/docs': 'Interactive API documentation'
        }
    }

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
    import sys
    
    # Check if running as API server or CLI tool
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        print("🚀 Starting PropShop API Server...")
        print("📊 Dashboard: http://localhost:3000")
        print("🔧 API Docs: http://localhost:5001/docs")
        print("⚡ API Endpoint: http://localhost:5001/api/analyze\n")
        uvicorn.run(app, host="0.0.0.0", port=5001)
    else:
        # Run as CLI tool
        asyncio.run(main())