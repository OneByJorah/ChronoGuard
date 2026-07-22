<div align="center">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white">
  <img src="https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge">
</div>

<br>

<div align="center">
  <h1>ChronoGuard</h1>
  <p><strong>Chrony NTP Client Dashboard</strong></p>
  <p>A sleek, live-updating web interface to monitor your Chrony NTP clients.</p>
  <p>
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#contributing">Contributing</a>
  </p>
</div>

---

## Screenshot

![ChronoGuard Dashboard](docs/screenshot.png)
*Live-updating NTP client dashboard with Chrony status and synchronization metrics.*

## Features

- **Live Dashboard** — Real-time updates without page refresh.
- **Chrony Integration** — Direct integration with chronyc command output.
- **Client Monitoring** — Track all NTP clients connected to your Chrony server.
- **Sync Status** — Visual indicators for synchronization health.
- **Offset Tracking** — Monitor time offset and frequency drift.
- **Lightweight** — Single-script Flask application, no database required.
- **Bootstrap 5 UI** — Clean, responsive interface.
- **AJAX Updates** — jQuery-powered automatic data refresh.

## Quick Start

```bash
git clone https://github.com/OneByJorah/ChronoGuard.git
cd ChronoGuard

pip install -r requirements.txt
python3 app.py
```

Open **http://localhost:5000** in your browser.

### systemd Service

```bash
sudo cp chroneguard.service /etc/systemd/system/
sudo systemctl enable chroneguard
sudo systemctl start chroneguard
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_APP` | `app.py` | Flask application entry point |
| `PORT` | `5000` | Server port |
| `HOST` | `0.0.0.0` | Bind address |
| `CHRONYC_PATH` | `/usr/bin/chronyc` | Path to chronyc binary |
| `REFRESH_INTERVAL` | `5000` | Dashboard refresh interval (ms) |

## Architecture

```
Browser (Bootstrap/jQuery) ──AJAX──▶ Flask App ──▶ chronyc ──▶ Chrony Server
                                              │
                                              └──▶ Time Sync Data
```

## Tech Stack

- **Backend**: Flask (Python 3.10+)
- **Frontend**: Bootstrap 5, jQuery, AJAX
- **NTP**: Chrony/chronyc integration
- **Deployment**: systemd service

## Project Structure

```
ChronoGuard/
├── app.py                 # Flask application
├── templates/
│   └── index.html         # Dashboard template
├── static/
│   ├── css/
│   │   └── style.css      # Custom styles
│   └── js/
│       └── app.js         # AJAX update logic
├── chroneguard.service    # systemd service file
├── requirements.txt       # Python dependencies
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/status` | GET | Chrony server status |
| `/api/clients` | GET | Connected NTP clients |
| `/api/sources` | GET | NTP source statistics |

## Dashboard Panels

| Panel | Description |
|-------|-------------|
| **Server Status** | Chrony daemon status and uptime |
| **Sync Mode** | Current synchronization mode (NTP, PPS, etc.) |
| **Sources** | NTP sources with reachability and offset |
| **Clients** | Connected clients with last query time |
| **System Time** | Current system time and offset from reference |

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

## Security

For security concerns, see [SECURITY.md](SECURITY.md). Please report vulnerabilities to **info@jorahone.com** — do not use public issues.

## License

MIT © Jhonattan L. Jimenez

---

<div align="center">
  <p>Live NTP client monitoring with Chrony.</p>
  <p><a href="https://github.com/OneByJorah">@OneByJorah</a></p>
</div>
