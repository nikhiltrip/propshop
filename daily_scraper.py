#!/usr/bin/env python3
"""
Daily scraper that runs once per day (midnight PST via cron).
Fetches props from PrizePicks and FanDuel, analyzes for +EV opportunities,
and saves results to JSON file for dashboard consumption.

Can also be run manually: python daily_scraper.py
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from prizepicks_scraper import fetch_props as fetch_prizepicks_props
from fanduel_scraper import fetch_odds as fetch_fanduel_odds

# Import analysis functions from main.py
from main import (
    BET_TYPES,
    american_to_probability,
    calculate_no_vig_probability,
    find_plus_ev_opportunities
)

DATA_FILE = Path(__file__).parent / "data" / "opportunities.json"

def format_opportunities_for_dashboard(opportunities_dict, fanduel_odds):
    """
    Convert opportunities dict to dashboard-friendly JSON format.
    """
    formatted_opps = []
    opp_id = 1
    
    for player, props in opportunities_dict.items():
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
            
            # Determine sport from stat type (simple heuristic)
            stat_lower = prop['stat'].lower()
            if any(term in stat_lower for term in ['passing', 'rushing', 'receiving', 'touchdown']):
                sport = 'NFL'
            elif any(term in stat_lower for term in ['points', 'rebounds', 'assists', '3-pointers', 'blocks', 'steals']):
                sport = 'NBA'
            elif any(term in stat_lower for term in ['goals', 'saves', 'shots']):
                sport = 'NHL'
            elif any(term in stat_lower for term in ['strikeouts', 'hits', 'runs', 'home runs']):
                sport = 'MLB'
            else:
                sport = 'Other'
            
            formatted_opps.append({
                'id': opp_id,
                'player': player,
                'sport': sport,
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
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'date': datetime.now().strftime('%Y-%m-%d')
    }

async def run_daily_scrape():
    """
    Run the full scraping pipeline and save to JSON.
    """
    print("\n" + "="*80)
    print("🌙 PROPSHOP DAILY SCRAPER")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p PST')}\n")
    
    try:
        # Step 1: Fetch PrizePicks props
        print("📊 Fetching props from PrizePicks...")
        prizepicks_props = await fetch_prizepicks_props()
        
        if not prizepicks_props:
            print("❌ Failed to fetch PrizePicks data (CAPTCHA or network error)")
            print("💡 Scraper will retry tomorrow at midnight")
            print("💡 Or run manually: python daily_scraper.py\n")
            return False
        
        print(f"✅ Fetched props for {len(prizepicks_props)} players from PrizePicks")
        
        # Step 2: Fetch FanDuel odds
        print("\n🎯 Fetching odds from FanDuel...")
        fanduel_odds = await fetch_fanduel_odds(prizepicks_props)
        
        if not fanduel_odds:
            print("❌ Failed to fetch FanDuel odds")
            return False
        
        print(f"✅ Fetched odds for {len(fanduel_odds)} players from FanDuel")
        
        # Step 3: Analyze for +EV opportunities
        print("\n💰 Analyzing for +EV opportunities...")
        opportunities = find_plus_ev_opportunities(fanduel_odds)
        
        if not opportunities:
            print("⚠️  No +EV opportunities found")
            # Still save empty results
            data = {
                'opportunities': [],
                'stats': {
                    'total_scanned': sum(len(props) for props in fanduel_odds.values()),
                    'plus_ev_found': 0,
                    'conversion_rate': 0,
                    'avg_edge': 0,
                    'best_edge': 0
                },
                'last_updated': datetime.utcnow().isoformat() + 'Z',
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        else:
            total_opps = sum(len(props) for props in opportunities.values())
            print(f"✅ Found {total_opps} +EV opportunities across {len(opportunities)} players")
            
            # Format for dashboard
            data = format_opportunities_for_dashboard(opportunities, fanduel_odds)
        
        # Step 4: Save to JSON file
        print(f"\n💾 Saving to {DATA_FILE}...")
        DATA_FILE.parent.mkdir(exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print("✅ Data saved successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Total props scanned: {data['stats']['total_scanned']}")
        print(f"   - +EV opportunities: {data['stats']['plus_ev_found']}")
        print(f"   - Conversion rate: {data['stats']['conversion_rate']}%")
        print(f"   - Average edge: {data['stats']['avg_edge']}%")
        print(f"   - Best edge: {data['stats']['best_edge']}%")
        
        print("\n" + "="*80)
        print("🎉 Daily scrape completed successfully!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    success = asyncio.run(run_daily_scrape())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
