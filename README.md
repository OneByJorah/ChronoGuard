# 🕐 NTP Dashboard

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-blue?logo=flask)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-blue?logo=bootstrap)](https://getbootstrap.com/)
[![MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Maintained by OneByJorah](https://img.shields.io/badge/Maintained%20by-OneByJorah-1E90FF?logo=github)](https://github.com/OneByJorah)

![NTP Dashboard Architecture](https://v3b.fal.media/files/b/0a9e5aae/JvZsxoUo9qYLoZsucNRBv_OFU9ZbVf.png)

> **NTP Dashboard**: TICC-DASH Time Information of Chrony Clients - Dashboard | A sleek, live‑updating web interface to monitor your Chrony NTP clients. Built with Python (Flask) · Bootstrap 5 · Vanilla JS + AJAX (jQuery) · Chrony/chronyc · systemd

---

## 📋 Overview

**NTP Dashboard** is a professional-grade Time Information and Chrony Client Monitoring Dashboard that provides real-time visibility into your network's time synchronization infrastructure. It features **live chrony client monitoring**, **drift analysis**, **server health tracking**, and **comprehensive time synchronization reporting** — all in a beautiful, responsive web interface.

> **Built with ❤️ by [OneByJorah](https://github.com/OneByJorah) for precise time synchronization monitoring.**

---

## 🏗️ Architecture

### High-Level System Architecture

```mermaid
flowchart TB
    subgraph Frontend["Web UI / API"]
        WEB[Web Interface<br/>Flask + Bootstrap 5]
        API[REST API<br/>Flask Blueprint]
    end

    subgraph Services["Core Services"]
        MONITOR[Client Monitor<br/>Real-time Status]
        DRIFT[Drift Analysis<br/>Offset Tracking]
        SERVER[Server Health<br/>Stratum + Delay]
        LOGS[Log Analysis<br/>Chrony Logs]
    end

    subgraph Data["Data Layer"]
        DB[(SQLite<br/>Config + History)]
        CACHE[(Redis<br/>Real-time Metrics)]
    end

    subgraph Integration["Integrations"]
        MSG[Telegram Bot<br/>Alerts]
        SLACK[Slack Alerts<br/>Incident Mgmt]
    end

    subgraph Security["Security"]
        AUTH[Authentication<br/>JWT + Session]
    end

    WEB <--> API
    API <--> MONITOR
    API <--> DRIFT
    API <--> SERVER
    API <--> LOGS
    MONITOR <--> DB
    DRIFT <--> DB
    SERVER <--> DB
    LOGS <--> DB
    API <--> CACHE
    MSG <--> API
    SLACK <--> API
    AUTH <--> DB

    style Frontend fill:#1a237e,stroke:#3f51b5,stroke-width:2px,color:#ffffff
    style Services fill:#2e7d32,stroke:#4caf50,stroke-width:2px,color:#ffffff
    style Data fill:#e65100,stroke:#ff9800,stroke-width:2px,color:#ffffff
    style Integration fill:#4a148c,stroke:#9c27b0,stroke-width:2px,color:#ffffff
    style Security fill:#c62828,stroke:#e53935,stroke-width:2px,color:#ffffff
```

---

## 🖼️ Screenshots

<div align="center">

### Dashboard Overview
![Dashboard](docs/dashboard.png)
*Main dashboard showing all chrony clients, server status, and drift analysis*

---

### Client Monitor
![Client Monitor](docs/clients.png)
*Real-time chrony client monitoring with offset tracking and status indicators*

---

### Server Health
![Server Health](docs/server-health.png)
*Server health monitoring with stratum tracking, delay metrics, and reliability scores*

---

### Drift Analysis
![Drift](docs/drift.png)
*Drift analysis with offset history, trend lines, and threshold alerts*

---

### Log Viewer
![Logs](docs/logs.png)
*Chrony log viewer with event filtering and pattern search*

---

### Settings
![Settings](docs/settings.png)
*Configuration management with server list, thresholds, and alert settings*

</div>

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🕐 **Live Client Monitor** | Real-time chrony client monitoring with offset tracking, status indicators, and health scoring |
| 📊 **Drift Analysis** | Comprehensive drift analysis with offset history, trend detection, and threshold alerts |
| 🖥️ **Server Health** | Server health monitoring with stratum tracking, delay metrics, jitter analysis, and reliability scoring |
| 📋 **Log Analysis** | Chrony log viewer with event filtering, pattern search, and automated anomaly detection |
| 🔔 **Alert System** | Multi-channel alerting with Telegram bot, Slack integration, email notifications, and push alerts |
| 🎨 **Beautiful UI** | Sleek, responsive web interface with Bootstrap 5, dark/light mode toggle, and smooth animations |
| 📊 **Dashboard Stats** | Real-time dashboard statistics with client counts, drift metrics, server health, and uptime tracking |
| 🔍 **Search & Filter** | Advanced search and filtering for clients, logs, and events with full-text search support |

---

## ⚡ Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/OneByJorah/ChronoGuard.git
cd ChronoGuard

# Install dependencies
pip install -r requirements.txt

# Run migrations
flask db upgrade

# Initialize admin user
python manage.py init-admin
```

### Configuration

Edit `config/settings.py`:

```python
# Server
SERVER_NAME = 'ChronoGuardboard.local'
SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key')

# Database
DATABASE_URL = 'sqlite:///ntp.db'

# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:***@192.168.1.100:6379')
```

### Running the Application

```bash
# Development
flask run --host=0.0.0.0 --port=5000

# Production
gunicorn --workers=4 --bind=0.0.0.0:5000 --timeout=120 app:create_app()
```

### Accessing the Web UI

```
http://localhost:5000
```

---

## 🔍 API Reference

### Base URL

```
http://localhost:5000/api/v1
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/clients` | GET | List all chrony clients |
| `/api/v1/clients/<id>` | GET | Get client details |
| `/api/v1/clients/<id>` | PUT | Update client settings |
| `/api/v1/clients/<id>` | DELETE | Delete client |
| `/api/v1/servers` | GET | List NTP servers |
| `/api/v1/servers/<id>` | GET | Get server details |
| `/api/v1/servers/<id>` | PUT | Update server settings |
| `/api/v1/servers/<id>` | DELETE | Delete server |
| `/api/v1/drift` | GET | Get drift analysis |
| `/api/v1/drift/history` | GET | Get drift history |
| `/api/v1/logs` | GET | List logs |
| `/api/v1/logs/search` | GET | Search logs |
| `/api/v1/logs/<id>` | GET | Get log entry |
| `/api/v1/health` | GET | System health check |
| `/api/v1/dashboard` | GET | Dashboard statistics |

---

## 📊 Monitoring

### System Health

```bash
# Check service status
sudo systemctl status ChronoGuardboard

# Check database connection
sqlite3 /var/lib/ChronoGuardboard/ntp.db "SELECT 1"

# Check Redis
redis-cli ping
```

### Logs

```bash
# Application logs
sudo tail -f /var/log/ChronoGuardboard/app.log

# Chrony logs
sudo tail -f /var/log/syslog | grep chrony
```

---

## 🔒 Security

### Network Security

- Session-based authentication with Flask-Login
- CSRF protection on all forms
- Rate limiting on API endpoints

### Authentication

- Session-based authentication with Flask-Login
- JWT tokens for API access
- Role-based access control (RBAC)

---

## 📚 Dependencies

### Python

```
Flask>=3.0.0
Flask-SQLAlchemy>=3.0.0
Flask-Migrate>=3.1.0
Flask-CORS>=4.0.0
Flask-Login>=0.6.0
PyYAML>=6.0
psycopg2-binary>=2.9.0
redis>=4.5.0
requests>=2.31.0
```

### System Dependencies

```
chrony>=4.2
chronyc>=4.2
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 📞 Support

For issues or questions, please open an issue on GitHub:

https://github.com/OneByJorah/ChronoGuard/issues

---

## 🙏 Acknowledgments

- **Flask**: Web framework by Armin Ronacher
- **Bootstrap**: Frontend framework by Twitter Bootstrap team

---

**Made with ❤️ by [OneByJorah](https://github.com/OneByJorah)**
