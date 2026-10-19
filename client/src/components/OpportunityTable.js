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
  const [minEdge, setMinEdge] = useState(0);
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
        row.model.edge >= Number(minEdge),
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
                <th>PP / FD line</th>
                <th>FD over / under</th>
                <th>No-vig estimate</th>
                <th>Edge (pp)</th>
                <th>Illustrative entry ROI</th>
                <th>Event starts</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>
                    <strong>{row.player}</strong>
                    <small>
                      <span className="sport-tag">{row.sport}</span> {row.stat}
                    </small>
                  </td>
                  <td>
                    <span className={`direction ${row.direction}`}>
                      {row.direction === "over" ? "More" : "Less"}
                    </span>
                  </td>
                  <td className="number">
                    {row.line} / {row.fanduel_line}
                  </td>
                  <td className="number">
                    {odds(row.over_odds)} / {odds(row.under_odds)}
                  </td>
                  <td className="number">
                    {row.no_vig_win_pct.toFixed(2)}%
                    <small>Break-even {row.model.threshold.toFixed(2)}%</small>
                  </td>
                  <td
                    className={row.model.edge > 0 ? "green number" : "number"}
                  >
                    {row.model.edge > 0 ? "+" : ""}
                    {row.model.edge.toFixed(2)}
                  </td>
                  <td className="number">
                    {row.model.equal_leg_roi_pct > 0 ? "+" : ""}
                    {row.model.equal_leg_roi_pct.toFixed(2)}%
                    <small>Equal, independent legs</small>
                  </td>
                  <td>
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
              : "Collect PrizePicks projections and FanDuel odds to see fresh, exact-line comparisons here."}
          </p>
          <span className="empty-caption">
            {opportunities.length
              ? `${opportunities.length} fresh matches available before filters`
              : "No sample bets. No estimated prices."}
          </span>
        </div>
      )}
      <div className="board-foot">
        {rows.length} shown · {opportunities.length} fresh matches{" "}
        <span>Line edits require new market odds.</span>
      </div>
    </section>
  );
}
