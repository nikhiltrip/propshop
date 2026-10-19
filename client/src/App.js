import React, { useEffect, useState } from "react";
import "./App.css";
import OpportunityTable from "./components/OpportunityTable";

export default function App() {
  const [data, setData] = useState(null);
  const [job, setJob] = useState({ state: "idle" });
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  useEffect(() => {
    let alive = true;
    let active = false;
    const load = async () => {
      if (active) return;
      active = true;
      try {
        const response = await fetch("/api/opportunities");
        if (!response.ok) throw new Error("API unavailable");
        const result = await response.json();
        if (alive) {
          setData(result);
          setJob(result.collection);
          setError("");
        }
      } catch (e) {
        if (alive)
          setError("Cannot reach the API. Start the server and try again.");
      } finally {
        active = false;
      }
    };
    load();
    const timer = setInterval(load, 3000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);
  async function collect() {
    setStarting(true);
    try {
      const response = await fetch("/api/trigger-scrape", { method: "POST" });
      const result = await response.json();
      if (!response.ok && response.status !== 409)
        throw new Error(result.message || "Could not start collection.");
      setJob(result.collection);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setStarting(false);
    }
  }
  const busy = starting || job.state === "running";
  const rows = data?.opportunities || [];
  return (
    <div className="app-shell">
      <header>
        <a className="brand" href="/">
          p<span>/</span> PropShop
        </a>
        <span className="header-note">PRIZEPICKS × FANDUEL</span>
        <span className={`status ${rows.length ? "connected" : ""}`}>
          {rows.length ? "Snapshot available" : "Awaiting data"}
        </span>
      </header>
      <main>
        <div className="intro">
          <div>
            <p className="eyebrow">THE PROP BOARD</p>
            <h1>Find the difference.</h1>
            <p className="muted">
              Exact lines. Two-sided odds. A clearer view of the market.
            </p>
          </div>
          <button className="primary" onClick={collect} disabled={busy}>
            {busy ? "Collecting sources…" : "↻ Collect fresh lines"}
          </button>
        </div>
        <div className="source-strip">
          <span>
            <i className="dot pp" />
            PrizePicks projections
          </span>
          <span>compared with</span>
          <span>
            <i className="dot fd" />
            FanDuel no-vig probabilities
          </span>
          <span className="timestamp">
            {data?.last_updated
              ? `Last snapshot ${new Date(data.last_updated).toLocaleString()}`
              : "No successful collection yet"}
          </span>
        </div>
        {error && (
          <div className="notice error" role="alert">
            {error}
          </div>
        )}
        {(job.state === "failed" || job.state === "interrupted") && (
          <div className="notice warning" role="alert">
            <strong>Collection needs attention. </strong>
            {job.message}
          </div>
        )}
        {busy && (
          <div className="notice" role="status">
            Collecting both boards. If a visible browser requests verification,
            complete it manually. Results appear when the collection finishes.
          </div>
        )}
        {data?.is_stale && data.last_updated && (
          <div className="notice warning">
            Snapshot expired. Comparisons older than 15 minutes are hidden.
          </div>
        )}
        <section className="metrics" aria-label="Collection summary">
          <div>
            <span>PrizePicks collected</span>
            <strong>{data?.stats?.prizepicks_collected ?? "—"}</strong>
            <small>Last successful run</small>
          </div>
          <div>
            <span>FanDuel collected</span>
            <strong>{data?.stats?.fanduel_collected ?? "—"}</strong>
            <small>Two-sided markets</small>
          </div>
          <div>
            <span>Fresh exact matches</span>
            <strong>{data?.stats?.total_scanned ?? 0}</strong>
            <small>Same player, stat, line & start</small>
          </div>
          <div>
            <span>Above model break-even</span>
            <strong className="green">{data?.stats?.plus_ev_found ?? 0}</strong>
            <small>Best qualifying entry model</small>
          </div>
        </section>
        <OpportunityTable opportunities={rows} loading={!data && !error} />
        <details className="method">
          <summary>How to read this board</summary>
          <p>
            FanDuel implied over and under probabilities are normalized to
            remove the margin. This is a market estimate, not a measured win
            rate. Edge is the difference in percentage points between that
            estimate and the selected entry model’s break-even rate.
          </p>
          <p>
            Illustrative entry ROI assumes every leg has the displayed
            probability and all legs are independent. It is not the expected
            return of one pick or a recommended lineup. Actual payouts,
            correlation, promotions and settlement rules can change the result.
            Integer lines, modified projections, started events and unknown
            markets are excluded.
          </p>
          <p>
            Models use standard Player Picks minimum-guarantee payouts,
            including partial Flex payouts, verified October 19, 2026. Check the
            actual entry payout before relying on a model.{" "}
            <a
              href="https://www.prizepicks.com/help-center/potential-outcomes"
              target="_blank"
              rel="noreferrer"
            >
              Payout source ↗
            </a>
          </p>
        </details>
        <footer>
          Snapshots refresh when collection succeeds. Prices can move between
          collection and review. No guaranteed profits.
        </footer>
      </main>
    </div>
  );
}
