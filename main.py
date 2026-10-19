"""CLI entry point and backwards-compatible analysis exports."""

from analysis import BET_TYPES, american_to_probability, calculate_no_vig_probability

if __name__ == "__main__":
    from daily_scraper import main

    main()
