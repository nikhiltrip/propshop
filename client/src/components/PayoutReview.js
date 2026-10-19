import React, { useEffect, useState } from "react";
import { parseSchedule } from "../payoutMath";

export default function PayoutReview({ model, definition, verification, onChange }) {
  const n = Number(model[0]);
  const [mode, setMode] = useState("standard");
  const [confirmed, setConfirmed] = useState(false);
  const [values, setValues] = useState(() => Array.from({ length: n + 1 }, (_, k) => String(definition?.payouts?.[k] ?? 0)));
  useEffect(() => { onChange(null); }, [onChange]);
  const parsed = parseSchedule(values);
  function publish(nextMode, nextValues, nextConfirmed) {
    const result = parseSchedule(nextValues);
    onChange(nextMode === "standard" ? null : {
      ...result, confirmed: nextConfirmed,
      error: result.error || (!nextConfirmed ? "Confirm that you copied every return from the actual entry before applying this schedule." : null),
    });
  }
  return <details className="payout-review">
    <summary>Check the payout behind your edge estimate</summary>
    <p>The standard schedule was manually checked {verification?.standard_schedule_checked_at || "on the date in the README"}. Your account’s actual entry payout is unverified. A standard projection label alone does not verify a payout.</p>
    <a href={verification?.source_url || "https://www.prizepicks.com/help-center/potential-outcomes"} target="_blank" rel="noreferrer">Official payout rules ↗</a>
    <label>Schedule to use
      <select value={mode} onChange={(e) => { setMode(e.target.value); publish(e.target.value, values, confirmed); }}>
        <option value="standard">Published standard {model}</option>
        <option value="custom" disabled={!definition?.payouts}>Enter the payout shown for my {n}-pick entry</option>
      </select>
    </label>
    {mode === "standard" ? <p className="muted">{definition?.payouts ? Array.from({ length: n + 1 }, (_, k) => `${k}/${n}: ${definition.payouts[k] || 0}x`).join(" · ") : "Collect a new snapshot to load the complete schedule."} — conditional estimates.</p> : <>
      <p>Copy total returns, including the entry fee, for every outcome. For a $10 entry that returns $30 total, enter 3. Include partial Flex returns; enter 0 where nothing is returned. This changes the hypothetical model for every row, not the sportsbook probabilities.</p>
      <div className="payout-inputs">{values.map((value, k) => <label key={k}>{k} of {n} correct
        <input type="number" min="0" max="10000" step="any" value={value} onChange={(e) => {
          const next = values.map((v, i) => i === k ? e.target.value : v);
          setValues(next); setConfirmed(false); publish(mode, next, false);
        }} />
      </label>)}</div>
      <label className="check"><input type="checkbox" checked={confirmed} onChange={(e) => { setConfirmed(e.target.checked); publish(mode, values, e.target.checked); }} />I copied all returns from the actual entry shown in PrizePicks.</label>
      {parsed.error ? <p role="alert">{parsed.error}</p> : <p>Equal-leg break-even: <strong>{parsed.threshold.toFixed(4)}%</strong>. {confirmed ? "Using your entered schedule for this session." : "Confirm the schedule to apply it."}</p>}
      <p className="muted">No account connection or independent verification. Entries are not saved. Switching entry model resets this form. Entry eligibility, correlation, ties and DNPs still require separate review.</p>
    </>}
  </details>;
}
