"""
TinyTraffic — Flask Dashboard Server
Serves a live HDMI-ready web dashboard showing LLM-generated
traffic summaries for Mohammed Bin Zayed Road, Abu Dhabi.

Usage:
    python display_server.py
Then open: http://raspberrypi.local:5001
"""

from flask import Flask, jsonify
from threading import Thread
import requests
import time
from datetime import datetime

app = Flask(__name__)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TOMTOM_API_KEY  = "YOUR_API_KEY_HERE"   # Get free key at developer.tomtom.com
ROAD_NAME       = "Mohammed Bin Zayed Road"
BBOX            = "54.35,24.40,54.55,24.50"
OLLAMA_URL      = "http://localhost:11434/api/generate"
MODEL           = "qwen2.5:0.5b"
REFRESH_SECONDS = 45
PORT            = 5001
# ──────────────────────────────────────────────────────────────────────────────

# Shared state updated by background thread
state = {
    "summary":      "Loading traffic data...",
    "raw":          "",
    "last_updated": "",
    "status":       "loading"
}


def fetch_traffic():
    """Fetch live incidents from TomTom for the configured road segment."""
    try:
        r = requests.get(
            "https://api.tomtom.com/traffic/services/5/incidentDetails",
            params={
                "key":              TOMTOM_API_KEY,
                "bbox":             BBOX,
                "fields":           "{incidents{type,properties{events{description},magnitudeOfDelay}}}",
                "language":         "en-GB",
                "timeValidityFilter": "present"
            },
            timeout=10
        )
        incidents = r.json().get("incidents", [])
        if not incidents:
            return "No incidents reported.", "clear"

        descriptions = []
        for inc in incidents[:6]:
            for event in inc.get("properties", {}).get("events", []):
                desc = event.get("description", "").strip()
                if desc and desc not in descriptions:
                    descriptions.append(desc)

        text = ", ".join(descriptions) if descriptions else "Minor disruptions."
        severity = "heavy" if any(
            w in text.lower() for w in ["closed", "stationary", "queuing"]
        ) else "moderate"
        return text, severity

    except Exception as e:
        return f"Data error: {e}", "unknown"


def summarize(traffic_text):
    """Pass incident text to on-device LLM and return natural-language summary."""
    prompt = (
        f"You are a traffic assistant for drivers on {ROAD_NAME} in Abu Dhabi. "
        f"Based on this live traffic data, write ONE short paragraph of 2-3 sentences "
        f"a driver can quickly glance at. Be specific, calm, and helpful. "
        f"Data: {traffic_text}"
    )
    try:
        r = requests.post(OLLAMA_URL, json={
            "model":  MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=60)
        return r.json().get("response", "Summary unavailable.")
    except Exception as e:
        return f"LLM error: {e}"


def background_loop():
    """Runs continuously: fetch → classify → infer → update state."""
    while True:
        raw, severity          = fetch_traffic()
        summary                = summarize(raw)
        state["summary"]       = summary
        state["raw"]           = raw
        state["last_updated"]  = datetime.now().strftime("%H:%M:%S")
        state["status"]        = severity
        print(f"[{state['last_updated']}] {severity.upper()} — {raw[:60]}...")
        time.sleep(REFRESH_SECONDS)


@app.route("/data")
def data():
    return jsonify(state)


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TinyTraffic</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #0a0a0a;
      color: white;
      font-family: "Segoe UI", sans-serif;
      height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 30px;
    }
    #header { font-size: 0.85rem; color: #888; letter-spacing: 3px;
              text-transform: uppercase; margin-bottom: 8px; }
    #road   { font-size: 1.9rem; font-weight: 700; margin-bottom: 28px; }
    #status-bar {
      width: 100%; max-width: 820px;
      background: #1a1a1a; border-radius: 10px;
      padding: 10px 20px; display: flex; align-items: center;
      gap: 10px; margin-bottom: 22px; font-size: 0.85rem; color: #aaa;
    }
    #dot { width: 13px; height: 13px; border-radius: 50%;
           background: #555; flex-shrink: 0; }
    #dot.clear    { background: #22c55e; }
    #dot.moderate { background: #f59e0b; }
    #dot.heavy    { background: #ef4444; }
    #dot.loading  { background: #3b82f6; }
    #card {
      width: 100%; max-width: 820px;
      background: #141414; border: 1px solid #2a2a2a;
      border-radius: 16px; padding: 36px 42px;
      line-height: 1.85; font-size: 1.28rem; color: #e5e5e5;
      min-height: 160px;
    }
    #raw       { margin-top: 18px; font-size: 0.72rem; color: #444;
                 max-width: 820px; text-align: center; }
    #timestamp { margin-top: 26px; font-size: 0.72rem; color: #333;
                 letter-spacing: 2px; }
  </style>
</head>
<body>
  <div id="header">Live Traffic Monitor</div>
  <div id="road">Mohammed Bin Zayed Road</div>
  <div id="status-bar">
    <div id="dot" class="loading"></div>
    <span id="status-text">Fetching data...</span>
  </div>
  <div id="card">Loading...</div>
  <div id="raw"></div>
  <div id="timestamp">—</div>

  <script>
    const labels = {
      clear:    "Traffic clear",
      moderate: "Moderate traffic",
      heavy:    "Heavy traffic / Incident",
      loading:  "Loading...",
      unknown:  "Status unknown"
    };
    async function update() {
      try {
        const res = await fetch("/data");
        const d   = await res.json();
        document.getElementById("card").innerText       = d.summary;
        document.getElementById("raw").innerText        = "RAW: " + d.raw;
        document.getElementById("timestamp").innerText  = "Last updated: " + d.last_updated;
        const dot = document.getElementById("dot");
        dot.className = d.status;
        document.getElementById("status-text").innerText = labels[d.status] || d.status;
      } catch(e) { console.log(e); }
    }
    update();
    setInterval(update, 5000);
  </script>
</body>
</html>"""


if __name__ == "__main__":
    print(f"🚦 TinyTraffic dashboard starting on port {PORT}")
    print(f"📍 Open http://raspberrypi.local:{PORT} in your browser\n")
    Thread(target=background_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, debug=False)
