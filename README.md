# TinyTraffic 🚦

**Edge-Deployed Language Model Inference for Near Real-Time Traffic Summarization on Resource-Constrained Hardware**

> UAEU CENG 440 Final Project | Department of Computer and Network Engineering, College of Information Technology, United Arab Emirates University

---

## Overview

TinyTraffic is a fully on-device traffic summarization system deployed on a **Raspberry Pi 4 Model B**. It fetches live incident data from the TomTom Traffic Incidents API, classifies severity, and uses a **4-bit quantized Qwen2.5-0.5B** language model served by Ollama to generate driver-readable summaries displayed on an HDMI dashboard.

All inference runs locally — **no cloud LLM dependency.**

**Road monitored:** Mohammed Bin Zayed Road, Abu Dhabi, UAE

---

## System Architecture

```
[TomTom API] → [Severity Classifier] → [Prompt Builder]
                                               ↓
                                    [Qwen2.5-0.5B INT4 on Pi]
                                               ↓
                                    [Flask Dashboard → HDMI Screen]
```

---

## Hardware Requirements

- Raspberry Pi 4 Model B (4GB RAM recommended)
- MicroSD card (16GB+)
- HDMI screen
- 4G hotspot or WiFi connection

## Software Requirements

- Raspberry Pi OS 64-bit (Bookworm, kernel 6.6)
- Python 3.11+
- [Ollama v0.3.x](https://ollama.com)
- TomTom API key — free tier at [developer.tomtom.com](https://developer.tomtom.com)

---

## Installation

```bash
# 1. Clone the repo onto your Pi (via SSH from your laptop)
git clone https://github.com/mustafanfj/TinyTraffic.git
cd TinyTraffic

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 5. Pull the quantized model (downloads ~400MB once)
ollama pull qwen2.5:0.5b
```

---

## Configuration

Open `display_server.py` and set your TomTom API key:

```python
TOMTOM_API_KEY = "YOUR_API_KEY_HERE"
```

The default bounding box targets Mohammed Bin Zayed Road, Abu Dhabi:
```python
BBOX = "54.35,24.40,54.55,24.50"
```

To monitor a different road, update the bounding box coordinates accordingly.

---

## Usage

### Run the live dashboard
```bash
python display_server.py
```
Open `http://raspberrypi.local:5001` in a browser on any device on the same network.

### Run the terminal-only version
```bash
python final_app.py
```

### Run the benchmark
```bash
python benchmark_v3.py
```
Results are saved to `results/benchmark_results.json`.

---

## Results

| Prompt Type | Mean Latency (s) | Std (s) | Min (s) | Max (s) |
|-------------|-----------------|---------|---------|---------|
| Heavy       | 17.74           | 9.25    | 2.00    | 36.78   |
| Moderate    | 27.22           | 15.05   | 2.09    | 45.63   |
| Clear       | 15.06           | 5.97    | 6.39    | 23.96   |
| **Overall** | **20.01**       | **11.66** | **2.00** | **45.63** |

**Key finding:** Mann–Whitney U test confirms a statistically significant throughput
reduction of **15.9% above 80°C** (U=181.0, p=0.0011), identifying passive cooling
as the primary performance bottleneck for sustained edge LLM inference.

---

## Paper

This project is accompanied by an IEEE-format research paper:

> M. Al Juboori, M. Almazrouei, T. Almazrouei, B. Mokhtar,
> *"TinyTraffic: Edge-Deployed Language Model Inference for Near Real-Time
> Traffic Summarization on Resource-Constrained Hardware,"*
> UAEU CENG 440, 2025.

---

## Project Structure

```
TinyTraffic/
├── final_app.py          # Terminal pipeline (fetch → infer → print)
├── display_server.py     # Flask dashboard server
├── benchmark_v3.py       # 30-run latency/thermal benchmark
├── requirements.txt      # Python dependencies
└── results/
    └── benchmark_results.json   # Raw benchmark output
```

---

## Team

| Name | Role |
|------|------|
| Mustafa Al Juboori | Lead Developer, System Architecture |
| Mohammed Almazrouei | API Integration, Testing |

**United Arab Emirates University**
Department of Computer and Network Engineering, College of Information Technology
