import { entryReturn, parseSchedule, customModel } from "./payoutMath";

test("complete Flex schedule includes partial returns and solves break-even", () => {
  const schedule = parseSchedule([0, 0, 0, 0, 0.4, 2, 25]);
  expect(schedule.error).toBeUndefined();
  expect(schedule.threshold).toBeCloseTo(54.20599, 4);
  expect(entryReturn(schedule.threshold / 100, schedule.payouts)).toBeCloseTo(1, 12);
  expect(entryReturn(0.5, [0, 0.5, 2])).toBe(0.75);
});

test("changed payout changes edge and full-entry ROI without changing probabilities", () => {
  const row = { no_vig_over: 60, no_vig_under: 40 };
  const before = { ...row };
  const standard = customModel(row, parseSchedule([0, 0, 3]));
  const changed = customModel(row, parseSchedule([0, 0, 4]));
  expect(changed.threshold).toBeCloseTo(50);
  expect(changed.edge).toBeCloseTo(10);
  expect(changed.equal_leg_roi_pct).toBeCloseTo(44);
  expect(changed.edge).toBeGreaterThan(standard.edge);
  expect(row).toEqual(before);
});

test.each([[0, "", 3], [0, " ", 3], [0, -1, 3], [0, Infinity, 3], [0, 4, 3], [1, 2, 3], [0, 0, 1], [0, 0, 10001]])("incomplete or unsupported payout schedule is rejected: %j", (...values) => {
  expect(parseSchedule(values).error).toBeTruthy();
});
