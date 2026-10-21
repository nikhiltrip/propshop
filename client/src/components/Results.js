import React, { useEffect, useState } from "react";

export default function Results({ collectionBusy }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  useEffect(() => {
    let alive = true, active = false;
    async function load() {
      if (active) return; active = true;
      try { const response = await fetch("/api/results"); if (!response.ok) throw new Error("History unavailable."); const result = await response.json(); if (alive) { setData(result); setError(""); } }
      catch (err) { if (alive) setError(err.message); }
      finally { active = false; }
    }
    load(); const timer = setInterval(load, 5000);
    return () => { alive = false; clearInterval(timer); };
  }, []);
  async function update() {
    setStarting(true);
    try { const response = await fetch("/api/refresh-results", { method: "POST" }); const result = await response.json(); if (!response.ok) throw new Error(result.message); setData((old) => ({ ...old, collection: result.collection })); }
    catch (err) { setError(err.message); }
    finally { setStarting(false); }
  }
  const busy = starting || data?.collection?.state === "running";
  const labels = { hypothetical_win: "Hypothetical win", hypothetical_loss: "Hypothetical loss", pending: "Pending", unresolved: "Needs review", tie: "Tie — settlement unmodeled" };
  return <section className="history-panel">
    <h2>Saved estimates and results</h2>
    <p>Estimates are frozen when first collected at each line and direction. These are hypothetical results against saved feed lines, not placed bets or confirmed PrizePicks payouts. Related props are not independent.</p>
    <button onClick={update} disabled={busy || collectionBusy}>{busy ? "Checking final stats…" : "Check final stats"}</button>
    <p className="muted">{data?.counts?.hypothetical_win || 0} hypothetical wins · {data?.counts?.hypothetical_loss || 0} hypothetical losses · {data?.counts?.unresolved || 0} need review · {data?.backfilled_count || 0} reconstructed observations excluded from prospective counts.</p>
    {error && <p role="alert">{error}</p>}
    {["failed", "interrupted"].includes(data?.collection?.state) && <p role="alert">{data.collection.message}</p>}
    {!data?.records?.length ? <p>No archived positive estimates yet. Collect fresh lines to begin; missing historical snapshots are never invented.</p> : <div className="history-list">{data.records.map((row) => <article key={row.key}>
      <strong>{row.player} · {row.direction === "over" ? "More" : "Less"} {row.line} {row.stat}</strong>
      <small>{row.probability.toFixed(2)}% pregame estimate · first saved {new Date(row.first_seen).toLocaleString()}{row.backfilled ? " · reconstructed later" : ""}</small>
      <p>{labels[row.outcome] || "Needs review"} · Actual: {row.actual ?? "not verified"}</p>
      <small>{row.reason || "Not checked yet."} {row.source_url && <a href={row.source_url} target="_blank" rel="noreferrer">Box score ↗</a>}</small>
    </article>)}</div>}
  </section>;
}
