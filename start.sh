#!/usr/bin/env bash
# muse-monitor/start.sh — Start muselsl stream + dashboard (runs in background)
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
MUSE_NAME="${MUSE_NAME:-Muse-73D3}"
PORT="${PORT:-3002}"
PID_FILE="/tmp/muse-monitor.pids"
LOG_FILE="/tmp/muse-monitor.log"

# ── Stop mode ──────────────────────────────────────────────────────────────
if [[ "${1:-}" == "stop" ]]; then
  if [ -f "$PID_FILE" ]; then
    while read -r pid; do
      kill "$pid" 2>/dev/null && echo "Stopped PID $pid"
    done < "$PID_FILE"
    rm -f "$PID_FILE"
    echo "🛑 Muse Monitor stopped"
  else
    echo "Not running"
  fi
  exit 0
fi

# ── Already running? ───────────────────────────────────────────────────────
if [ -f "$PID_FILE" ] && kill -0 "$(head -1 "$PID_FILE")" 2>/dev/null; then
  echo "✅ Already running — http://localhost:${PORT}"
  open "http://localhost:${PORT}" 2>/dev/null
  exit 0
fi

# ── 1. muselsl stream ──────────────────────────────────────────────────────
if ! pgrep -f "muselsl stream" > /dev/null 2>&1; then
  echo "🎧 Starting muselsl stream for ${MUSE_NAME}…"
  muselsl stream --name "${MUSE_NAME}" >> "$LOG_FILE" 2>&1 &
  echo $! >> "$PID_FILE"
  sleep 3
else
  echo "✅ muselsl already running"
fi

# ── 2. Node deps ───────────────────────────────────────────────────────────
if [ ! -d "${SKILL_DIR}/node_modules" ]; then
  echo "📦 Installing Node deps…"
  cd "${SKILL_DIR}" && npm install --silent
fi

# ── 3. Start server in background ─────────────────────────────────────────
cd "${SKILL_DIR}"
nohup node server.js >> "$LOG_FILE" 2>&1 &
echo $! >> "$PID_FILE"
sleep 1

# ── 4. Open browser ────────────────────────────────────────────────────────
open "http://localhost:${PORT}" 2>/dev/null

echo "🧠 Muse Monitor running in background"
echo "   Dashboard: http://localhost:${PORT}"
echo "   Logs:      $LOG_FILE"
echo "   To stop:   bash $0 stop"
