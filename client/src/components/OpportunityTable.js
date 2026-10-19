import React, { useState } from "react";

const names = [
  "6-Pick Flex",
  "5-Pick Flex",
  "4-Pick Flex",
  "3-Pick Flex",
  "2-Pick Flex",
  "6-Pick Power",
  "5-Pick Power",
  "4-Pick Power",
  "3-Pick Power",
  "2-Pick Power",
];
const odds = (n) => (n > 0 ? `+${n}` : String(n));
export default function OpportunityTable({ opportunities, loading }) {
  const [search, setSearch] = useState("");
  const [sport, setSport] = useState("All");
  const [model, setModel] = useState("6-Pick Flex");
  const [minEdge, setMinEdge] = useState("");
  const [sort, setSort] = useState("edge");
  const [positiveOnly, setPositiveOnly] = useState(true);
  const rows = opportunities
    .map((row) => ({ ...row, model: row.models.find((m) => m.type === model) }))
    .filter(
      (row) =>
        row.model &&
        row.player.toLowerCase().includes(search.trim().toLowerCase()) &&
        (sport === "All" || sport === row.sport) &&
        (!positiveOnly || row.model.edge > 0) &&
        (minEdge === "" || row.model.edge >= Number(minEdge)),
    )
    .sort((a, b) =>
      sort === "player"
        ? a.player.localeCompare(b.player)
        : b.model.edge - a.model.edge,
    );
  return (
    <section className="board">
      <div className="board-heading">
        <h2>
          Market comparisons <span>{rows.length}</span>
        </h2>
        <span className="muted">
          Sorted by {sort === "edge" ? "estimated edge" : "player"}
        </span>
      </div>
      <div className="filters">
        <label>
          Search player
          <input
            placeholder="Player name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <label>
          Sport
          <select value={sport} onChange={(e) => setSport(e.target.value)}>
            {["All", "NBA", "NFL", "MLB", "NHL"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          Entry model
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            {names.map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
        <label>
          Min edge (pp)
          <input
            type="number"
            step="0.5"
            min="-50"
            max="50"
            value={minEdge}
            onChange={(e) => setMinEdge(e.target.value)}
          />
        </label>
        <label>
          Sort
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="edge">Highest edge</option>
            <option value="player">Player A–Z</option>
          </select>
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={positiveOnly}
            onChange={(e) => setPositiveOnly(e.target.checked)}
          />
          Positive edge only
        </label>
      </div>
      {rows.length > 0 ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Player / market</th>
                <th>Pick</th>
                <th>PrizePicks line</th>
                <th>Sportsbook quotes</th>
                <th>No-vig consensus</th>
                <th>Edge (pp)</th>
                <th>Illustrative entry ROI</th>
                <th>Event starts</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td data-label="Player / market">
                    <strong>{row.player}</strong>
                    <small>
                      <span className="sport-tag">{row.sport}</span> {row.stat}
                    </small>
                  </td>
                  <td data-label="Pick">
                    <span className={`direction ${row.direction}`}>
                      {row.direction === "over" ? "More" : "Less"}
                    </span>
                  </td>
                  <td className="number" data-label="PrizePicks line">{row.line}</td>
                  <td className="number" data-label="Sportsbook quotes">
                    <details className="quotes">
                      <summary>
                        {row.book_count || 1}{" "}
                        {row.book_count > 1 ? "books" : "book"}
                      </summary>
                      {(
                        row.book_comparisons || [
                          {
                            name: "FanDuel",
                            over_odds: row.over_odds,
                            under_odds: row.under_odds,
                            no_vig_over: row.no_vig_over,
                          },
                        ]
                      ).map((book) => (
                        <div key={book.name}>
                          <strong>{book.name}</strong>
                          <small>
                            O {odds(book.over_odds)} / U {odds(book.under_odds)}{" "}
                            · O {book.no_vig_over?.toFixed(2)}%
                          </small>
                        </div>
                      ))}
                      {row.provider_updated_at && (
                        <small>
                          Feed record updated{" "}
                          {new Date(
                            row.provider_updated_at,
                          ).toLocaleTimeString()}
                        </small>
                      )}
                      <a
                        href={
                          row.source_url ||
                          "https://www.scoresandodds.com/nfl/props"
                        }
                        target="_blank"
                        rel="noreferrer"
                      >
                        View source ↗
                      </a>
                    </details>
                  </td>
                  <td className="number" data-label="Consensus likelihood">
                    <div>More {row.no_vig_over.toFixed(2)}%</div>
                    <div>Less {row.no_vig_under.toFixed(2)}%</div>
                    <small>Break-even {row.model.threshold.toFixed(2)}%</small>
                  </td>
                  <td data-label="Edge (percentage points)"
                    className={row.model.edge > 0 ? "green number" : "number"}
                  >
                    {row.model.edge > 0 ? "+" : ""}
                    {row.model.edge.toFixed(2)}
                  </td>
                  <td className="number" data-label="Illustrative entry ROI">
                    {row.model.equal_leg_roi_pct > 0 ? "+" : ""}
                    {row.model.equal_leg_roi_pct.toFixed(2)}%
                    <small>Equal, independent legs</small>
                  </td>
                  <td data-label="Event starts">
                    {new Date(row.start_time).toLocaleString()}
                    <small>{row.event}</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty">
          <span className="empty-icon">↗</span>
          <h3>
            {loading
              ? "Loading the board…"
              : opportunities.length
                ? "No comparisons match these filters"
                : "Your board starts with real data"}
          </h3>
          <p>
            {opportunities.length
              ? "Try a different entry model, sport, or minimum edge."
              : "Collect PrizePicks lines and sportsbook odds to see fresh, exact-line comparisons here."}
          </p>
          <span className="empty-caption">
            {opportunities.length
              ? `${opportunities.length} fresh matches available before filters`
              : "Waiting for fresh source data."}
          </span>
        </div>
      )}
      <div className="board-foot">
        {rows.length} shown · {opportunities.length} fresh matches{" "}
        <span>
          Standard-payout model · confirm line and payout in PrizePicks
        </span>
      </div>
    </section>
  );
}
