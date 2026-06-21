# ChronoGuard — TICC Dash (Chrony NTP Dashboard)

**Version:** v1.0  
**Status:** Active Development  
**Repository:** https://github.com/OneByJorah/ChronoGuard

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Features](#features)
- [Getting Started](#getting-started)
- [Service Management](#service-management)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Overview

ChronoGuard (TICC Dash) is a lightweight Flask dashboard for monitoring a local Chrony NTP server/client. It parses live chrony client status and presents it as a responsive web UI showing NTP status, drop counts, polling intervals, and last-seen timestamps.

Designed for quick visibility into NTP health on edge and server infrastructure.

---

## Architecture

Client browser → Flask backend (`ticc-dash.py`) → `chronyc` CLI parsing → rendered HTML dashboard.

No database layer: the app reads live `chronyc` output on each request and returns a parsed snapshot.

---

## Technology Stack

| Layer | Stack |
|---|---|
| Runtime | Linux (Ubuntu 22.04+, Raspberry Pi OS) |
| Backend | Python / Flask |
| Metrics Source | Chrony (`chronyc`) |
| Frontend | HTML5 (server-rendered template strings) |
| Assets | SVG / PNG logo |
| VCS | Git + GitHub (`github.com/OneByJorah/ChronoGuard`) |

---

## Features

- **Live NTP status**: parses `chronyc` client output for connected peers/clients.
- **Metrics dashboard**: NTP state, drops, polling interval, last command timestamps.
- **Responsive layout**: CSS grid adapts from 3-column desktop down to mobile.
- **Zero database**: stateless reads from chrony, low overhead.

---

## Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/OneByJorah/ChronoGuard.git
cd ChronoGuard

# 2. Install dependencies
pip install -r requirements.txt  # or: pip install flask

# 3. Ensure chrony is installed and running
sudo apt-get install chrony
sudo systemctl enable --now chronyd

# 4. Start the dashboard
python3 ticc-dash.py
```

Visit `http://localhost:5000`.

---

## Service Management

```bash
# Quick test
python3 ticc-dash.py

# Production: run behind a reverse proxy or systemd unit
# Example systemd unit location: systemd/pirouter.service (adapt as needed)
```

---

## Project Structure

```
ChronoGuard/
├── ticc-dash.py           # Flask app + live chrony parser
├── install_ticc_dash.sh
├── uninstall_ticc_dash.sh
├── static/img/
│   ├── ticc-dash-logo.png
│   └── ticc-dash-logo-embedded.svg
└── README.md
```

---

## Screenshots

### TICC Dash
![TICC Dash](static/img/ticc-dash-logo.png)

---

## Contributing

1. Create a feature branch off `main`.
2. Test against a live `chronyd` instance before submitting.
3. Submit a PR with description and screenshots for UI changes.

---

## License

MIT

---

## Author

Built by **Jhonattan L. Jimenez**.
