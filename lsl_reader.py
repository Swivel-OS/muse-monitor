#!/usr/bin/env python3
"""
lsl_reader.py — MUSE EEG LSL → JSON bridge
Reads LSL stream from muselsl, classifies brain state, emits JSON to stdout.
One JSON line per 2-second window.

Output format:
  {"state": "FLOW", "emoji": "🌊", "detail": "Alpha=0.42", "powers": {...}}
"""

import sys
import json
import time
import numpy as np
from datetime import datetime

try:
    from pylsl import StreamInlet, resolve_byprop
except ImportError:
    print(json.dumps({"error": "pylsl not installed. Run: pip3 install pylsl"}), flush=True)
    sys.exit(1)

WINDOW_SEC = 2
SAMPLE_RATE = 256
WINDOW_SAMPLES = WINDOW_SEC * SAMPLE_RATE

BANDS = {
    "delta":    (1,  4),
    "theta":    (4,  8),
    "alpha":    (8,  13),
    "beta_low": (13, 20),
    "beta_high":(20, 30),
}

EMOJIS = {
    "FLOW":     "🌊",
    "STRESS":   "⚡",
    "CREATIVE": "🎨",
    "ACTIVE":   "⚙️",
    "UNKNOWN":  "❓",
}

# Default thresholds (can be overridden by vibe mode via stdin in future)
THRESHOLDS = {
    "FLOW":     {"band": "alpha",     "value": 0.35},
    "STRESS":   {"band": "beta_high", "value": 0.25},
    "CREATIVE": {"band": "theta",     "value": 0.30},
    "ACTIVE":   {"band": "beta_low",  "value": 0.30},
}


def bandpower(data, sf, band):
    """Relative band power via FFT."""
    fft_vals = np.abs(np.fft.rfft(data))
    fft_freqs = np.fft.rfftfreq(len(data), 1.0 / sf)
    band_mask  = (fft_freqs >= band[0]) & (fft_freqs <= band[1])
    total_mask = (fft_freqs >= 1)       & (fft_freqs <= 50)
    total = fft_vals[total_mask].sum()
    if total == 0:
        return 0.0
    return float(fft_vals[band_mask].sum() / total)


def classify_state(powers, thresholds=None):
    th = thresholds or THRESHOLDS
    alpha     = powers["alpha"]
    theta     = powers["theta"]
    beta_low  = powers["beta_low"]
    beta_high = powers["beta_high"]

    if alpha     >= th["FLOW"]["value"]:
        return "FLOW",     f"Alpha={alpha:.2f}"
    elif beta_high >= th["STRESS"]["value"]:
        return "STRESS",   f"HighBeta={beta_high:.2f}"
    elif theta     >= th["CREATIVE"]["value"]:
        return "CREATIVE", f"Theta={theta:.2f}"
    elif beta_low  >= th["ACTIVE"]["value"]:
        return "ACTIVE",   f"LowBeta={beta_low:.2f}"
    else:
        return "UNKNOWN",  f"A={alpha:.2f} T={theta:.2f} BL={beta_low:.2f} BH={beta_high:.2f}"


def main():
    sys.stderr.write("🧠 Scanning for MUSE LSL stream...\n")
    sys.stderr.flush()

    streams = resolve_byprop("type", "EEG", timeout=15)
    if not streams:
        msg = {"error": "No MUSE stream found. Run: muselsl stream --name Muse-73D3"}
        print(json.dumps(msg), flush=True)
        sys.exit(1)

    inlet = StreamInlet(streams[0])
    info  = inlet.info()
    sys.stderr.write(f"✅ Connected: {info.name()} @ {info.nominal_srate()}Hz\n")
    sys.stderr.flush()

    buffer = []

    while True:
        sample, _ = inlet.pull_sample(timeout=1.0)
        if sample is None:
            continue
        buffer.append(sample[:4])  # TP9, AF7, AF8, TP10

        if len(buffer) < WINDOW_SAMPLES:
            continue

        # Trim buffer to rolling window
        buffer = buffer[-WINDOW_SAMPLES:]
        data   = np.array(buffer)
        signal = data.mean(axis=1)
        signal -= signal.mean()  # remove DC offset

        powers = {band: bandpower(signal, SAMPLE_RATE, freq)
                  for band, freq in BANDS.items()}

        state, detail = classify_state(powers)
        ts = datetime.now().strftime("%H:%M:%S")

        payload = {
            "ts":     ts,
            "state":  state,
            "emoji":  EMOJIS.get(state, ""),
            "detail": detail,
            "powers": {k: round(v, 4) for k, v in powers.items()},
        }
        print(json.dumps(payload), flush=True)


if __name__ == "__main__":
    main()
