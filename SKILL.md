---
name: muse-monitor
description: "MUSE 2 EEG brainwave dashboard. Starts the muselsl stream (if not running) and launches a full-screen ambient brain state monitor at localhost:3002. Use when: user wants to see live EEG data, brain state, or MUSE headband output."
metadata:
  {
    "openclaw": {
      "emoji": "🧠",
      "requires": { "anyBins": ["muselsl", "node"] }
    }
  }
---

# Muse Monitor Skill

Live brainwave dashboard for MUSE 2 EEG headband.

## What it does

1. Checks if `muselsl stream --name Muse-73D3` is running; starts it if not
2. Starts a Node.js server at `http://localhost:3002`
3. Opens the dashboard in the browser

## How to invoke

```bash
bash ~/.openclaw/workspace/skills/muse-monitor/start.sh
```

Or with a custom device name:
```bash
MUSE_NAME="Muse-XXXX" bash ~/.openclaw/workspace/skills/muse-monitor/start.sh
```

## Dashboard features

- **Brain state**: Big centered display — 🌊 FLOW / ⚡ STRESS / 🎨 CREATIVE / ⚙️ ACTIVE
- **Band power bars**: Alpha, Theta, Beta Low, Beta High, Delta — animated fill
- **State history**: Last 10 state changes with timestamps
- **Vibe modes**: FOCUS / MEDITATE / CREATIVE / HYPE — changes color palette
- **Fullscreen**: ⛶ button for TV/AirPlay mode

## Stack

- `lsl_reader.py` — reads LSL stream, classifies brain state, emits JSON to stdout
- `server.js` — Express + WebSocket, spawns Python reader, fans updates to browser
- `public/index.html` — ambient full-screen dashboard (fleet aesthetic)

## Device

- Device name: `Muse-73D3`
- MAC: `00FC5701-54C9-0C79-6081-E5BEFBC7FA63`
- Sample rate: 256 Hz, 4 EEG channels (TP9, AF7, AF8, TP10)

## Thresholds (adjustable in lsl_reader.py)

| State    | Condition              | Default |
|----------|------------------------|---------|
| FLOW     | alpha > threshold      | 0.35    |
| STRESS   | beta_high > threshold  | 0.25    |
| CREATIVE | theta > threshold      | 0.30    |
| ACTIVE   | beta_low > threshold   | 0.30    |

## Troubleshooting

- **No stream found**: Run `muselsl stream --name Muse-73D3` manually and check Bluetooth
- **Port in use**: `PORT=3003 bash start.sh`
- **pylsl missing**: `pip3 install pylsl`
- **Node deps**: `cd ~/.openclaw/workspace/skills/muse-monitor && npm install`
