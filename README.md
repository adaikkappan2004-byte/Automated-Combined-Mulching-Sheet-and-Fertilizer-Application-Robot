# AgriBot Firmware

**v18.6.0 — Production Ready**

A Raspberry Pi-based semi-autonomous agricultural robot with a Flask web UI. Supports manual driving, guided row-traversal with fertilizer dispensing, Hall-sensor odometry, session reporting, and multilingual UI (English, Tamil, Hindi, Telugu, Kannada, Urdu).

---

## Hardware

| Component | GPIO (BCM) |
|-----------|-----------|
| Left motor PWM | 12 |
| Left motor DIR | 13 |
| Right motor PWM | 18 |
| Right motor DIR | 19 |
| Fertilizer servo | 23 |
| Fertilizer LED | 24 |
| Hall sensor | 17 |

---

## Setup

### 1. Clone & install

```bash
git clone <repo-url>
cd agribot
pip install -r requirements.txt
```

### 2. Configure secrets

Copy the example env file and edit it:

```bash
cp .env.example .env
nano .env
```

`.env` contents:

```
AGRIBOT_PASSWORD=your_secure_password
AGRIBOT_SECRET_KEY=your_random_flask_secret
```



### 3. Run (requires root for GPIO + port 80)

```bash
sudo python agribot.py
```

Then open `http://<pi-ip>` in a browser on the same network.

---

## Features

- **Manual mode** — D-pad style touch/mouse control with ramp-up/ramp-down
- **Guided mode** — Automated row traversal with configurable length, spacing, and row count
- **Fertilizer control** — Servo-actuated valve with interpolated flow-rate table; auto-closed at row end to prevent over-dispensing
- **Hall sensor odometry** — Pulse-based distance tracking with time-based fallback
- **Session report** — Downloadable PDF with distance, fertilizer dispensed, battery usage, and event log
- **Abort safety** — Emergency stop works mid-turn (100 ms poll), motors halt within ~50 ms

---

## Configuration

Field parameters (length, spacing, rows, pulses/meter) persist in `field_config.json` between reboots. This file is excluded from git — it is generated at runtime.

---


