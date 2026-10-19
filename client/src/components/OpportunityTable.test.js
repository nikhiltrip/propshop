import React, { act } from "react";
import { createRoot } from "react-dom/client";
import OpportunityTable from "./OpportunityTable";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

// Synthetic rows used only in this test. Never published by the application.
const base = {
  id: "fixture",
  player: "Synthetic Player",
  sport: "NBA",
  stat: "Points",
  direction: "over",
  line: 25.5,
  fanduel_line: 25.5,
  over_odds: -150,
  under_odds: 120,
  no_vig_win_pct: 56.8,
  no_vig_over: 56.8,
  no_vig_under: 43.2,
  start_time: "2030-01-01T12:00:00Z",
  event: "Synthetic event",
  models: [
    { type: "6-Pick Flex", edge: 2, threshold: 54.8, equal_leg_roi_pct: 10 },
    {
      type: "2-Pick Power",
      edge: -0.94,
      threshold: 57.74,
      equal_leg_roi_pct: -3,
    },
  ],
};

test("changing entry model re-filters against the selected payout threshold", () => {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<OpportunityTable opportunities={[base]} />));
  expect(container.textContent).toContain("Synthetic Player");
  const model = Array.from(container.querySelectorAll("select")).find(
    (s) => s.value === "6-Pick Flex",
  );
  act(() => {
    model.value = "2-Pick Power";
    model.dispatchEvent(new Event("change", { bubbles: true }));
  });
  expect(container.textContent).not.toContain("Synthetic Player");
  expect(container.textContent).toContain("No comparisons match these filters");
  const positiveOnly = container.querySelector('input[type="checkbox"]');
  act(() => positiveOnly.click());
  expect(container.textContent).toContain("Synthetic Player");
  expect(container.textContent).toContain("-0.94");
  act(() => root.unmount());
  container.remove();
});

test("missing source data shows an empty board without invented odds", () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  act(() => root.render(<OpportunityTable opportunities={[]} />));
  expect(container.querySelector("tbody")).toBeNull();
  expect(container.textContent).toContain("Your board starts with real data");
  act(() => root.unmount());
});
