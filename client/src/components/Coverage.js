import React from "react";
import LineCheck from "./LineCheck";

export default function Coverage({ source, opportunities, unmatched }) {
  return <details className="coverage">
    <summary>Coverage: {opportunities.length} comparable · {unmatched.length} collected without an estimate</summary>
    <p>These counts describe this source, not the full PrizePicks board. Missing stats or games cannot be inferred. Started and expired lines are hidden.</p>
    {source?.coverage?.map((league) => <div key={league.sport} className="coverage-league">
      <strong>{league.sport}</strong>: {league.prizepicks_lines ?? "—"} lines collected · {opportunities.filter((r) => r.sport === league.sport).length} fresh comparisons · {league.events_scanned ?? "—"} games scanned
      <p className="muted">{Object.entries(league.market_counts || {}).map(([stat, count]) => `${stat}: ${count}`).join(" · ") || "No category counts in this snapshot."}</p>
      {league.unsupported_markets?.length > 0 && <p className="muted">Unsupported categories: {league.unsupported_markets.join(", ")}</p>}
    </div>)}
    {unmatched.length > 0 && <>
      <h3>Collected lines without a probability estimate</h3>
      <p>Different sportsbook lines are never substituted. These lines are not ranked as edge opportunities.</p>
      <div className="unmatched-list">{unmatched.map((row) => <div key={row.id}>
        <strong>{row.player}</strong> · {row.sport} · {row.stat} {row.line}
        <small>{row.reason}</small>
        {row.recheck && <LineCheck row={row} />}
      </div>)}</div>
    </>}
  </details>;
}
