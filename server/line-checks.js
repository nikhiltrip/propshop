const normalize = (value) => String(value || "").normalize("NFKD").replace(/[^a-zA-Z0-9]/g, "").toLowerCase();
function lineKey(row) {
  return [row.sport, normalize(row.player), normalize(row.stat), Date.parse(row.start_time)].join(":");
}
function applyChecks(rows, checks, now) {
  const accepted = [], quarantined = [];
  for (const row of rows) {
    const check = checks[lineKey(row)];
    if (!check) { accepted.push({ ...row, line_status: "unverified" }); continue; }
    const age = now - Date.parse(check.checked_at);
    const fresh = Number.isFinite(age) && age >= 0 && age <= 900000;
    const matches = check.actual_line === row.line && check.variant === "standard";
    if (fresh && matches) {
      accepted.push({ ...row, line_status: "user_confirmed", line_checked_at: check.checked_at });
    } else {
      quarantined.push({ id: row.id, player: row.player, sport: row.sport, stat: row.stat,
        line: row.line, actual_line: check.actual_line, start_time: row.start_time,
        observed_at: row.prizepicks_observed_at, recheck: true,
        reason: !fresh ? "Previous manual line check expired; recheck before ranking this market."
          : check.variant !== "standard" ? "Modified or unknown projection: standard payout model is not eligible."
          : `Known line mismatch: source ${row.line}, observed PrizePicks ${check.actual_line}. Recheck required.` });
    }
  }
  return { accepted, quarantined };
}
module.exports = { lineKey, applyChecks };
