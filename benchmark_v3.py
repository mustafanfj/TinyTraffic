"""
TinyTraffic — Benchmark Script v3
Runs 30 inference trials (10 per prompt type) and records
latency, throughput, and CPU temperature for each run.

Usage:
    python benchmark_v3.py

Output:
    - Console summary table
    - results/benchmark_results.json
"""

import requests
import time
import subprocess
import json
import os
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
OLLAMA_URL     = "http://localhost:11434/api/generate"
MODEL          = "qwen2.5:0.5b"
RUNS_PER_TYPE  = 10   # 10 × 3 types = 30 runs total
INTER_RUN_GAP  = 3    # seconds between runs
OUTPUT_DIR     = "results"
OUTPUT_FILE    = os.path.join(OUTPUT_DIR, "benchmark_results.json")
# ──────────────────────────────────────────────────────────────────────────────

PROMPTS = {
    "heavy": (
        "Slow traffic, Closed, Stationary traffic. "
        "Summarize for a driver on Mohammed Bin Zayed Road Abu Dhabi in 2-3 sentences."
    ),
    "moderate": (
        "Queuing traffic, Slow traffic. "
        "Summarize for a driver on Mohammed Bin Zayed Road Abu Dhabi in 2-3 sentences."
    ),
    "clear": (
        "No incidents reported. Traffic flowing normally. "
        "Summarize for a driver on Mohammed Bin Zayed Road Abu Dhabi in 2-3 sentences."
    ),
}


def get_temp():
    """Read CPU temperature via vcgencmd (Raspberry Pi only)."""
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return float(out.strip().replace("temp=", "").replace("'C", ""))
    except Exception:
        return -1.0   # returns -1 if not on Pi


def run_benchmark():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []
    run_num = 0

    print(f"TinyTraffic Benchmark — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Model: {MODEL}  |  Runs per type: {RUNS_PER_TYPE}  |  Total: {RUNS_PER_TYPE * 3}")
    print(f"{'Run':<5} {'Type':<10} {'Latency(s)':<12} {'Tokens':<8} {'Tok/s':<8} {'Temp(C)'}")
    print("-" * 58)

    for label, prompt in PROMPTS.items():
        for i in range(RUNS_PER_TYPE):
            run_num += 1
            temp  = get_temp()
            start = time.time()

            r = requests.post(OLLAMA_URL, json={
                "model":  MODEL,
                "prompt": prompt,
                "stream": False
            }, timeout=120)

            elapsed  = round(time.time() - start, 2)
            response = r.json().get("response", "")
            tokens   = len(response.split())
            toks     = round(tokens / elapsed, 2) if elapsed > 0 else 0

            results.append({
                "run":          run_num,
                "type":         label,
                "latency_s":    elapsed,
                "tokens":       tokens,
                "toks_per_sec": toks,
                "temp_c":       temp,
                "response":     response
            })

            print(f"{run_num:<5} {label:<10} {elapsed:<12} {tokens:<8} {toks:<8} {temp}")
            time.sleep(INTER_RUN_GAP)

    # ── Summary stats ─────────────────────────────────────────────────────────
    print("\n" + "=" * 58)
    print("SUMMARY BY PROMPT TYPE")
    print("=" * 58)
    for label in PROMPTS.keys():
        subset = [r for r in results if r["type"] == label]
        lats   = [r["latency_s"]    for r in subset]
        toks   = [r["toks_per_sec"] for r in subset]
        temps  = [r["temp_c"]       for r in subset]
        mean_l = sum(lats) / len(lats)
        std_l  = (sum((x - mean_l) ** 2 for x in lats) / len(lats)) ** 0.5
        print(f"\n{label.upper()}:")
        print(f"  Latency  — mean: {mean_l:.2f}s  "
              f"min: {min(lats):.2f}s  max: {max(lats):.2f}s  std: {std_l:.2f}s")
        print(f"  Tok/s    — mean: {sum(toks)/len(toks):.2f}  "
              f"min: {min(toks):.2f}  max: {max(toks):.2f}")
        print(f"  Temp     — mean: {sum(temps)/len(temps):.1f}C  "
              f"min: {min(temps):.1f}C  max: {max(temps):.1f}C")

    # ── Save results ──────────────────────────────────────────────────────────
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    run_benchmark()
