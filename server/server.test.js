const { test, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "propshop-test-"));
process.env.PROPSHOP_DATA_DIR = dir;
const { createApp, snapshot } = require("./server");
after(() => fs.rmSync(dir, { recursive: true, force: true }));

test("snapshot suppresses legacy, stale and started opportunities", () => {
  const now = Date.now();
  const iso = (n) => new Date(n).toISOString();
  assert.deepEqual(snapshot().opportunities, []);
  fs.writeFileSync(
    path.join(dir, "opportunities.json"),
    JSON.stringify({ opportunities: [{ id: 1 }] }),
  );
  assert.deepEqual(snapshot().opportunities, []);
  const row = {
    id: "one",
    edge: 2,
    start_time: iso(now + 3600000),
    prizepicks_observed_at: iso(now - 1000),
    fanduel_observed_at: iso(now - 1000),
  };
  const data = {
    schema_version: 2,
    last_updated: iso(now - 1000),
    opportunities: [row, { ...row, start_time: iso(now - 1000) }],
    stats: {},
  };
  fs.writeFileSync(path.join(dir, "opportunities.json"), JSON.stringify(data));
  assert.equal(snapshot(now).count, 1);
  assert.equal(snapshot(now + 900001).count, 0);
});

test("collection responds once, locks, exposes failure and allows retry", async () => {
  let child;
  const app = createApp({
    spawnProcess: () => {
      child = new EventEmitter();
      child.stdout = new EventEmitter();
      child.stderr = new EventEmitter();
      return child;
    },
  });
  const server = app.listen(0, "127.0.0.1");
  await new Promise((resolve) => server.once("listening", resolve));
  const url = `http://127.0.0.1:${server.address().port}`;
  try {
    assert.equal(
      (
        await fetch(url + "/api/trigger-scrape", {
          method: "POST",
          headers: { origin: "https://other.test" },
        })
      ).status,
      403,
    );
    assert.equal(
      (await fetch(url + "/api/trigger-scrape", { method: "POST" })).status,
      202,
    );
    assert.equal(
      (await fetch(url + "/api/trigger-scrape", { method: "POST" })).status,
      409,
    );
    child.emit("close", 1);
    assert.equal(
      (await (await fetch(url + "/api/scrape-status")).json()).state,
      "failed",
    );
    assert.equal(
      (await fetch(url + "/api/trigger-scrape", { method: "POST" })).status,
      202,
    );
    child.emit("error", new Error("spawn ENOENT"));
    child.emit("close", -2);
    assert.equal(
      (await (await fetch(url + "/api/scrape-status")).json()).state,
      "failed",
    );
    assert.equal((await fetch(url + "/api/opportunities/missing")).status, 404);
    assert.equal((await fetch(url + "/health")).status, 200);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
