# PropShop remaining work

See [README.md](README.md) for the current implementation and verified limitations.

1. Restore source access; browser verification was followed by an access restriction during the October 19, 2026 test.
2. Capture successful current source payloads and add regression fixtures without user/account data. Validate both parser schemas and stat/league navigation.
3. Reconcile event IDs and start times across the two sources, preserving exact period and line matching.
4. Measure market coverage and collection duration; load missing player-market tabs explicitly.
5. If using a provider, verify current PrizePicks and FanDuel player-prop coverage before purchasing or implementing it.
6. Add deployment authentication and source-appropriate refresh limits before exposing the local API publicly.

No live end-to-end success, profitability, or production readiness is claimed.
