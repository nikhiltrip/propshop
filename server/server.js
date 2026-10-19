const express = require("express");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

const ROOT = path.resolve(__dirname, "..");
const DATA_DIR = process.env.PROPSHOP_DATA_DIR || path.join(ROOT, "data");
const MAX_AGE_MS = 15 * 60 * 1000;
function readJSON(name) {
  try {
    return JSON.parse(fs.readFileSync(path.join(DATA_DIR, name), "utf8"));
  } catch (error) {
    return null;
  }
}
function fresh(timestamp, now) {
  const age = now - Date.parse(timestamp);
  return Number.isFinite(age) && age >= 0 && age <= MAX_AGE_MS;
}
function snapshot(now = Date.now()) {
  const data = readJSON("opportunities.json");
  const valid = data?.schema_version === 2 && Array.isArray(data.opportunities);
  const stale = !valid || !fresh(data.last_updated, now);
  const rows = stale
    ? []
    : data.opportunities.filter(
        (row) =>
          fresh(row.prizepicks_observed_at, now) &&
          fresh(row.sportsbook_observed_at || row.fanduel_observed_at, now) &&
          Date.parse(row.start_time) > now,
      );
  const positive = rows.filter((r) => r.edge > 0);
  return {
    success: true,
    opportunities: rows,
    count: rows.length,
    is_stale: stale,
    last_updated: valid ? data.last_updated : null,
    source: valid ? data.source : null,
    source_info: valid ? data.source_info : null,
    models: valid ? data.models : {},
    methodology: valid ? data.methodology : null,
    stats: {
      ...(valid ? data.stats : {}),
      total_scanned: rows.length,
      plus_ev_found: positive.length,
      best_edge: Math.max(0, ...positive.map((r) => r.edge)),
    },
    message: !valid
      ? "No verified snapshot yet. Collect both sources to start."
      : stale
        ? "Snapshot is older than 15 minutes. Collect fresh lines to see comparisons."
        : null,
  };
}
function createApp({ spawnProcess = spawn } = {}) {
  const app = express();
  app.use(express.json({ limit: "8kb" }));
  let job = { state: "idle" };
  let child = null;
  const status = () => {
    if (job.state !== "idle") return job;
    const disk = readJSON("collection-status.json");
    // A previous server/process may have died; never promise it is still running.
    return disk?.state === "running"
      ? {
          ...disk,
          state: "interrupted",
          message: "Previous collection did not finish. Retry collection.",
        }
      : disk || job;
  };
  app.get("/health", (req, res) =>
    res.json({ status: "ok", service: "propshop" }),
  );
  app.get("/api/opportunities", (req, res) =>
    res.json({ ...snapshot(), collection: status() }),
  );
  app.get("/api/stats", (req, res) =>
    res.json({ success: true, stats: snapshot().stats }),
  );
  app.get("/api/opportunities/:id", (req, res) => {
    const row = snapshot().opportunities.find(
      (r) => String(r.id) === req.params.id,
    );
    return row
      ? res.json({ success: true, opportunity: row })
      : res.status(404).json({
          success: false,
          message: "No fresh opportunity with that ID.",
        });
  });
  app.get("/api/scrape-status", (req, res) => res.json(status()));
  app.post("/api/trigger-scrape", (req, res) => {
    // Local dashboard only. Reject cross-site requests to this unauthenticated mutation.
    const origin = req.get("origin");
    const allowed = new Set([
      `http://localhost:${process.env.PORT || 3001}`,
      "http://localhost:3000",
      `http://127.0.0.1:${process.env.PORT || 3001}`,
      "http://127.0.0.1:3000",
    ]);
    if (origin && !allowed.has(origin))
      return res
        .status(403)
        .json({ success: false, message: "Local requests only." });
    if (child)
      return res.status(409).json({
        success: false,
        message: "Collection already running.",
        collection: job,
      });
    job = {
      state: "running",
      started_at: new Date().toISOString(),
      message: "Collecting public PrizePicks lines and sportsbook quotes.",
    };
    const venv = path.join(ROOT, ".venv", "bin", "python");
    const python =
      process.env.PYTHON || (fs.existsSync(venv) ? venv : "python3");
    let timedOut = false;
    let timer;
    const finish = (state, message) => {
      clearTimeout(timer);
      child = null;
      job = { ...job, state, message, finished_at: new Date().toISOString() };
    };
    try {
      child = spawnProcess(python, [path.join(ROOT, "daily_scraper.py")], {
        cwd: ROOT,
        env: process.env,
        stdio: ["ignore", "pipe", "pipe"],
      });
      // Drain streams without returning raw browser logs or provider credentials to clients.
      child.stdout.on("data", () => {});
      child.stderr.on("data", () => {});
      let launchFailed = false;
      child.once("error", () => {
        launchFailed = true;
        finish(
          "failed",
          "Could not start Python. Check PYTHON and requirements.txt.",
        );
      });
      child.once("close", (code) => {
        if (launchFailed) return;
        const savedStatus = readJSON("collection-status.json");
        const saved =
          savedStatus &&
          Date.parse(savedStatus.started_at) >= Date.parse(job.started_at)
            ? savedStatus
            : null;
        finish(
          code === 0 ? "succeeded" : "failed",
          timedOut
            ? "Collection timed out after 10 minutes. Last snapshot retained."
            : code === 0
              ? "Fresh comparison published."
              : saved?.message ||
                "Collection failed. Check Python and browser dependencies.",
        );
      });
      timer = setTimeout(
        () => {
          timedOut = true;
          child?.kill("SIGTERM");
        },
        10 * 60 * 1000,
      );
      timer.unref();
      // Exactly one response; job completion is read from the status endpoint.
      return res.status(202).json({ success: true, collection: job });
    } catch (error) {
      finish("failed", "Could not start the collector.");
      return res.status(500).json({ success: false, collection: job });
    }
  });
  const build = path.join(ROOT, "client", "build");
  app.use(express.static(build));
  app.get("*", (req, res) =>
    req.path.startsWith("/api/")
      ? res.status(404).json({ success: false })
      : fs.existsSync(path.join(build, "index.html"))
        ? res.sendFile(path.join(build, "index.html"))
        : res
            .status(404)
            .send(
              "Run npm run build in client/, or start the React development server.",
            ),
  );
  return app;
}
if (require.main === module) {
  const port = Number(process.env.PORT || 3001);
  createApp().listen(port, "127.0.0.1", () =>
    console.log(`PropShop: http://localhost:${port}`),
  );
}
module.exports = { createApp, snapshot };
