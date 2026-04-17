"""
TinyTraffic — Terminal Pipeline
Fetches live traffic data from TomTom API and generates
LLM summaries using Qwen2.5-0.5B via Ollama.

Usage:
    python final_app.py
"""

import requests
import time
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TOMTOM_API_KEY = "YOUR_API_KEY_HERE"   # Get free key at developer.tomtom.com
ROAD_NAME      = "Mohammed Bin Zayed Road"
BBOX           = "54.35,24.40,54.55,24.50"   # Abu Dhabi — MBZ Road corridor
OLLAMA_URL     = "http://localhost:11434/api/generate"
MODEL          = "qwen2.5:0.5b"
REFRESH_SECONDS = 45
# ──────────────────────────────────────────────────────────────────────────────


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
            return "No incidents reported. Traffic is flowing normally."

        descriptions = []
        for inc in incidents[:6]:
            for event in inc.get("properties", {}).get("events", []):
                desc = event.get("description", "").strip()
                if desc and desc not in descriptions:
                    descriptions.append(desc)

        return ", ".join(descriptions) if descriptions else "Minor disruptions detected."

    except Exception as e:
        return f"Data fetch error: {e}"


def summarize(traffic_text):
    """Send traffic data to local LLM and get a driver-friendly summary."""
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


def display(summary, raw):
    """Print formatted output to terminal."""
    print("\n" + "=" * 55)
    print(f"  🚦 {ROAD_NAME}")
    print(f"  🕐 {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 55)
    print(f"  RAW: {raw[:100]}...")
    print("-" * 55)
    print(f"  {summary}")
    print("=" * 55)


# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚗 TinyTraffic started — refreshing every {REFRESH_SECONDS}s")
    print(f"📍 Monitoring: {ROAD_NAME}\n")

    while True:
        raw     = fetch_traffic()
        summary = summarize(raw)
        display(summary, raw)
        time.sleep(REFRESH_SECONDS)
