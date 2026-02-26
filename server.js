/**
 * muse-monitor server.js
 * Express + WebSocket server. Spawns lsl_reader.py, fans JSON state to all clients.
 */

const express   = require("express");
const { WebSocketServer } = require("ws");
const { spawn } = require("child_process");
const path      = require("path");
const http      = require("http");

const PORT     = 3002;
const SKILL_DIR = __dirname;
const READER   = path.join(SKILL_DIR, "lsl_reader.py");

const app    = express();
const server = http.createServer(app);
const wss    = new WebSocketServer({ server, path: "/ws" });

// Serve dashboard
app.use(express.static(path.join(SKILL_DIR, "public")));

// Track connected clients
const clients = new Set();
wss.on("connection", (ws) => {
  clients.add(ws);
  console.log(`[ws] client connected (total: ${clients.size})`);

  // Send last known state immediately on connect
  if (lastState) ws.send(JSON.stringify(lastState));

  ws.on("close", () => {
    clients.delete(ws);
    console.log(`[ws] client disconnected (total: ${clients.size})`);
  });
});

function broadcast(obj) {
  const msg = JSON.stringify(obj);
  for (const ws of clients) {
    if (ws.readyState === 1 /* OPEN */) ws.send(msg);
  }
}

// ── Python LSL reader ──────────────────────────────────────────────────────
let lastState = null;
let readerProc = null;
let lineBuffer = "";

function startReader() {
  console.log("[reader] spawning lsl_reader.py …");
  readerProc = spawn("python3", [READER], {
    cwd: SKILL_DIR,
    stdio: ["ignore", "pipe", "pipe"],
  });

  readerProc.stdout.on("data", (chunk) => {
    lineBuffer += chunk.toString();
    const lines = lineBuffer.split("\n");
    lineBuffer = lines.pop(); // incomplete line stays in buffer

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const payload = JSON.parse(trimmed);
        if (payload.error) {
          console.error("[reader] ERROR:", payload.error);
          broadcast({ type: "error", message: payload.error });
          return;
        }
        lastState = { type: "state", ...payload };
        broadcast(lastState);
      } catch (_) {
        // not JSON — ignore
      }
    }
  });

  readerProc.stderr.on("data", (d) => process.stderr.write(`[reader] ${d}`));

  readerProc.on("exit", (code, sig) => {
    console.warn(`[reader] exited (code=${code} sig=${sig}), restarting in 3s …`);
    readerProc = null;
    setTimeout(startReader, 3000);
  });
}

// ── Start ─────────────────────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`\n🧠 Muse Monitor`);
  console.log(`   Dashboard: http://localhost:${PORT}`);
  console.log(`   WebSocket: ws://localhost:${PORT}/ws\n`);
  startReader();
});

// Clean shutdown
process.on("SIGINT",  () => { readerProc?.kill(); process.exit(0); });
process.on("SIGTERM", () => { readerProc?.kill(); process.exit(0); });
