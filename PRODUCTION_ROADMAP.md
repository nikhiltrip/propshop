# PropShop remaining work

The default public-comparison collector now works end to end. See [README.md](README.md) for setup and methodology.

1. Track source latency and compare third-party PrizePicks lines against the live account board. The feed can lag and does not verify projection modifiers or account payouts.
2. Add a properly licensed data contract before relying on the public website endpoint for uptime or public distribution.
3. Extend explicitly supported stat aliases/markets only with source evidence and period/settlement tests. NBA currently has no props in the source.
4. Add a model for ties/voids and correlated unequal-leg entries before expanding beyond the current conditional standard-payout analysis.
5. Add authentication and deployment monitoring before exposing the local API publicly.
6. Direct browser adapters remain optional and unverified; their dedicated profile supports manual login persistence when source access permits it.

Successful retrieval and positive modeled edge do not establish realized profits or verified entry eligibility.
