# test_odds.py - Test the +EV logic with C.J. Stroud example

from main import american_to_probability, calculate_no_vig_probability, BET_TYPES

# C.J. Stroud 239.5 passing yards
player = "C.J. Stroud"
stat = "Passing Yards"
line = 239.5
over_odds = -118
under_odds = -112

print("="*80)
print(f"Testing: {player} - {stat} {line}")
print(f"FanDuel Odds: Over {over_odds:+d} | Under {under_odds:+d}")
print("="*80)

# Step 1: Convert to implied probabilities
print("\n--- Step 1: American Odds → Implied Probability ---")
over_implied = american_to_probability(over_odds)
under_implied = american_to_probability(under_odds)
print(f"Over {over_odds}: {over_implied:.2f}%")
print(f"Under {under_odds}: {under_implied:.2f}%")
print(f"Total (includes vig): {over_implied + under_implied:.2f}%")

# Step 2: Calculate no-vig probabilities
print("\n--- Step 2: Remove Vig → True Market Probability ---")
no_vig_over, no_vig_under = calculate_no_vig_probability(over_odds, under_odds)
print(f"No-Vig Over: {no_vig_over:.2f}%")
print(f"No-Vig Under: {no_vig_under:.2f}%")
print(f"Total (should be 100%): {no_vig_over + no_vig_under:.2f}%")

# Step 3: Check against PrizePicks thresholds
print("\n--- Step 3: Check Against PrizePicks Bet Type Thresholds ---")

print("\n🔍 OVER Analysis:")
over_qualifies = []
for bet_name, bet_info in BET_TYPES.items():
    threshold = bet_info['min_win_pct']
    if no_vig_over >= threshold:
        edge = no_vig_over - threshold
        over_qualifies.append({
            'bet_type': bet_name,
            'edge': edge,
            'payout': bet_info['payout']
        })
        print(f"  ✅ {bet_name}: {no_vig_over:.2f}% > {threshold:.2f}% (edge: +{edge:.2f}%, pays {bet_info['payout']}x)")
    else:
        shortfall = threshold - no_vig_over
        print(f"  ❌ {bet_name}: {no_vig_over:.2f}% < {threshold:.2f}% (need +{shortfall:.2f}%)")

print("\n🔍 UNDER Analysis:")
under_qualifies = []
for bet_name, bet_info in BET_TYPES.items():
    threshold = bet_info['min_win_pct']
    if no_vig_under >= threshold:
        edge = no_vig_under - threshold
        under_qualifies.append({
            'bet_type': bet_name,
            'edge': edge,
            'payout': bet_info['payout']
        })
        print(f"  ✅ {bet_name}: {no_vig_under:.2f}% > {threshold:.2f}% (edge: +{edge:.2f}%, pays {bet_info['payout']}x)")
    else:
        shortfall = threshold - no_vig_under
        print(f"  ❌ {bet_name}: {no_vig_under:.2f}% < {threshold:.2f}% (need +{shortfall:.2f}%)")

# Summary
print("\n" + "="*80)
print("📊 SUMMARY")
print("="*80)
if over_qualifies or under_qualifies:
    print("💰 +EV OPPORTUNITY FOUND!")
    if over_qualifies:
        print(f"\n✅ OVER qualifies for {len(over_qualifies)} bet type(s)")
        for qual in sorted(over_qualifies, key=lambda x: x['edge'], reverse=True):
            print(f"   • {qual['bet_type']}: +{qual['edge']:.2f}% edge")
    if under_qualifies:
        print(f"\n✅ UNDER qualifies for {len(under_qualifies)} bet type(s)")
        for qual in sorted(under_qualifies, key=lambda x: x['edge'], reverse=True):
            print(f"   • {qual['bet_type']}: +{qual['edge']:.2f}% edge")
else:
    print("❌ NOT +EV - No bet types qualify")
    print(f"   Need to find props with higher win probability")
    print(f"   Minimum threshold: 54.21% (6-Pick Flex)")
    print(f"   This prop: Over {no_vig_over:.2f}% | Under {no_vig_under:.2f}%")
