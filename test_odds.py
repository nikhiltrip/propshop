"""Synthetic CLI calculation example, not a live market or a profitability claim."""

from analysis import BET_TYPES, calculate_no_vig_probability

if __name__ == "__main__":
    over, under = calculate_no_vig_probability("-118", "-112")
    print(
        f"Synthetic prices: Over -118 / Under -112; no-vig {over:.2f}% / {under:.2f}%"
    )
    for name, model in BET_TYPES.items():
        print(f"{name}: equal-leg break-even {model['min_win_pct']:.4f}%")
