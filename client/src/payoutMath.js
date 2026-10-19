// Full hit-count schedules; values are total returns including the entry fee.
export function entryReturn(probability, payouts) {
  let distribution = [1];
  for (let i = 0; i < payouts.length - 1; i++) {
    const next = Array(distribution.length + 1).fill(0);
    distribution.forEach((chance, hits) => {
      next[hits] += chance * (1 - probability);
      next[hits + 1] += chance * probability;
    });
    distribution = next;
  }
  return distribution.reduce((sum, chance, hits) => sum + chance * payouts[hits], 0);
}

export function parseSchedule(values) {
  const payouts = values.map((v) => Number(v));
  if (values.length < 3 || values.length > 7 || values.some((v) => String(v).trim() === "") ||
      payouts.some((v) => !Number.isFinite(v) || v < 0 || v > 10000)) {
    return { error: "Enter every total-return multiplier, including 0 for losing outcomes (0–10,000x)." };
  }
  if (payouts.some((v, i) => i > 0 && v < payouts[i - 1]) || payouts[0] >= 1 || payouts.at(-1) <= 1) {
    return { error: "Returns must not decrease as correct picks increase, with 0-correct below 1x and all-correct above 1x." };
  }
  let low = 0, high = 1;
  for (let i = 0; i < 70; i++) {
    const mid = (low + high) / 2;
    if (entryReturn(mid, payouts) < 1) low = mid;
    else high = mid;
  }
  return { payouts, threshold: (low + high) / 2 * 100 };
}

export function customModel(row, schedule) {
  const p = Math.max(row.no_vig_over, row.no_vig_under);
  return {
    type: "User-entered payout", threshold: schedule.threshold,
    edge: p - schedule.threshold,
    equal_leg_roi_pct: (entryReturn(p / 100, schedule.payouts) - 1) * 100,
  };
}
