import React, { useState } from "react";

export default function LineCheck({ row }) {
  const [value, setValue] = useState("");
  const [variant, setVariant] = useState("unknown");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function save(event) {
    event.preventDefault(); setBusy(true);
    try {
      const response = await fetch("/api/line-checks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: row.id, actual_line: Number(value), variant }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.message || "Could not save check.");
      setMessage(result.matched ? "You confirmed this line for 15 minutes. Payout is still unverified." : "Mismatch or modified projection recorded. This market will leave the ranked board.");
    } catch (error) { setMessage(error.message); }
    finally { setBusy(false); }
  }
  return <details className="line-check">
    <summary>{row.line_status === "user_confirmed" ? "Line confirmed by you" : "Feed line only · check it"}</summary>
    <form onSubmit={save}>
      <p>Check this exact player, stat and game in PrizePicks. A matching line does not confirm payout or lineup eligibility.</p>
      <label>Line shown in PrizePicks<input required type="number" min="0" step="any" value={value} onChange={(e) => setValue(e.target.value)} /></label>
      <label>Projection type<select value={variant} onChange={(e) => setVariant(e.target.value)}><option value="unknown">Unknown</option><option value="standard">Standard (no modifier)</option><option value="goblin">Goblin</option><option value="demon">Demon</option></select></label>
      <button disabled={busy || value.trim() === ""}>Save my observation</button>
      <p role="status">{message}</p>
    </form>
  </details>;
}
