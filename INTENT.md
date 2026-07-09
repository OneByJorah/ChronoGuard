# INTENT.md — J1-PIPELINE Phase -1 (ORACLE)

**Repository:** `OneByJorah/ChronoGuard`
**Analysis Date:** 2026-07-05
**Analyst:** J1-PIPELINE ORACLE (read-only)
**Status:** Intent Reconstructed

---

## What This System Does

ChronoGuard (branded **TICC Dash** — "Time Information of Chrony Clients – Dashboard") is a lightweight, stateless Flask web dashboard that monitors a local Chrony NTP server/client. It parses live `chronyc clients` CLI output on each HTTP request and renders a responsive, dark-themed HTML table showing:

| Metric | Description |
|---|---|
| **NTP** | Number of NTP packets exchanged with each client |
| **Drop** | Number of dropped packets per client |
| **Int / IntL** | Polling interval (current / long-term) |
| **Last** | Time since last packet from each client |
| **Cmd** | Number of command packets exchanged |

The dashboard provides:
- **Live auto-refresh** (every 1 second via jQuery polling `/data` endpoint)
- **Sorting** by IP address, drop count (descending), or last-seen (recent first)
- **Client search/filter** by any field
- **Expandable detail rows** showing per-client metrics tiles
- **Dark/light theme toggle** persisted to localStorage
- **Summary bar** with OK / Warning / Critical client counts (threshold: ≥10 drops = Critical, >0 drops = Warning)
- **Expand-all / collapse-all** toggle for detail rows

### Operational Role

ChronoGuard is an **observability tool** for edge and server infrastructure where NTP health is critical. It is deployed alongside a running `chronyd` service and provides instant visual feedback on NTP synchronization quality. It is consumed by:

- **System administrators** monitoring NTP health across connected peers
- **Edge infrastructure operators** who need quick visibility into time sync without SSHing into every box
- **JorahOne internal infrastructure** as a lightweight monitoring adjunct for servers running Chrony

The system has **no database**, **no authentication**, **no persistent state** — it is a read-only window into live `chronyc` output, designed for LAN/internal use.

---

## Why This Was Built

### Real Problem

NTP (Network Time Protocol) health is critical for distributed systems, logging, certificate validation, and database consistency. When NTP drifts or drops occur, the symptoms are subtle and hard to diagnose — skewed timestamps, authentication failures, replication lag. The standard tool for checking NTP client status is `chronyc clients` on the command line, which:

- Requires SSH access to every machine
- Outputs raw columnar text that is hard to scan at a glance
- Provides no historical trending or visual alerting
- Is impractical for multi-server environments where an operator needs to check NTP health across many boxes quickly

### Why Existing Tools Were Insufficient

| Tool | Gap |
|---|---|
| **`chronyc clients` CLI** | Raw text, no visualization, no remote access, no alerting |
| **`ntpq -p`** | Legacy NTP tool, not compatible with Chrony's richer client data |
| **Grafana + Prometheus + node_exporter** | Overkill for a single-box NTP view; requires full observability stack; no Chrony client-level metrics exposed by default |
| **Nagios / Icinga / Zabbix** | Heavyweight; require agent installation; designed for alerting, not real-time visual browsing |
| **Custom shell scripts** | No web UI, no interactivity, no sorting/filtering |

What was needed was a **zero-dependency, single-file, deploy-and-forget** dashboard that gives an operator the same information as `chronyc clients` but in a browser — readable at a glance, sortable, filterable, and auto-refreshing.

### What Triggered Development

The original project (`ticc-dash`) was created by `anoniemerd` as a standalone utility. JorahOne adopted and forked it into `OneByJorah/ChronoGuard` because:

1. **JorahOne operates edge infrastructure** (routers, servers, IoT gateways) where NTP accuracy is critical for log correlation and certificate validation.
2. **Existing monitoring was CLI-only** — operators had to SSH into each box and run `chronyc clients` manually.
3. **The original `ticc-dash` repo** provided a clean, minimal Flask app that solved exactly this problem with no architectural overhead.
4. **The fork allowed JorahOne to** migrate raw source URLs, apply portfolio standardization (ruff auto-fixes), add security auditing, and integrate it into the J1 pipeline lifecycle.

The migration from `anoniemerd/ticc-dash` → `OneByJorah/ChronoGuard` is visible in the git history: commit `01f42f0` ("fix: migrate raw source URLs from anoniemerd/ticc-dash to OneByJorah/ChronoGuard") and the `upstream` remote still pointing to the original repo.

### Ecosystem Fit

```
JorahOne Infrastructure
├── Chrony (NTP daemon)          ← time sync provider
├── ChronoGuard / TICC Dash      ← NTP observability layer
├── EdgeRouter                   ← edge networking (separate repo)
├── Hermes Agent                 ← AI orchestration (separate repo)
└── Other J1 observability tools
```

ChronoGuard fills the **NTP observability** niche in the JorahOne ecosystem. It is a small, focused tool — not a platform — that complements the broader infrastructure monitoring strategy. It sits alongside Chrony on the same host and provides a web UI for what would otherwise require a terminal.

---

## Operational Classification

**Classification: BETA**

Evidence:
- **Version label**: `v1.0` in README — initial release, no semantic versioning history
- **No tests**: No `tests/` directory, no test files, no test runner configured
- **No Docker support**: No `Dockerfile`, no `docker-compose.yml` — deployment is bare-metal only via systemd
- **No `requirements.txt`**: Dependencies (Flask, Gunicorn) are installed ad-hoc in the install script; no pinned versions
- **No CI/CD beyond CodeQL**: CodeQL workflow exists but no build/test/deploy pipeline
- **No health checks**: The systemd service has no `HealthCheck` or `RestartSec` tuning beyond `Restart=always`
- **No monitoring integration**: No Prometheus metrics, no health endpoint, no logging beyond systemd journal
- **No authentication**: Dashboard is open on port 5000 with no auth — suitable only for trusted/internal networks
- **Security audit present**: Commit `35c30e7` ("audit(ChronoGuard): sanitize email references") shows security awareness
- **Community readiness**: Has CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, MIT license, issue/PR templates, Dependabot
- **Deployment model**: Single-systemd-unit, Gunicorn behind no reverse proxy by default (nginx suggested but not configured)
- **No backup/DR**: Stateless design means no data to back up, but no recovery procedure documented either

**Verdict**: Functional and useful, but not production-hardened. Lacks testing, containerization, dependency pinning, and operational runbooks. Appropriate for internal/scratch use.

---

## Key Architectural Decisions

1. **Stateless, no-database design** — Every request shells out to `chronyc clients` and parses the output fresh. This eliminates data persistence concerns and keeps the app trivially simple, at the cost of no historical trending.

2. **Server-rendered HTML with inline template strings** — The entire frontend (HTML, CSS, JS) is embedded as a Python triple-quoted string in `ticc-dash.py`. No separate frontend build step, no static file serving beyond the logo. This keeps deployment to a single file.

3. **`sudo chronyc clients` via subprocess** — The Flask app runs as a regular user but needs root to execute `chronyc clients`. The install script creates a passwordless sudoers rule for `/usr/bin/chronyc` only. This is a pragmatic security tradeoff.

4. **Gunicorn as production WSGI server** — The systemd service runs Gunicorn instead of Flask's dev server, with `PYTHONUNBUFFERED=1` for log visibility.

5. **Bootstrap 5 + jQuery from CDN** — No local vendoring of frontend dependencies. The dashboard relies on CDN availability, which is acceptable for internal/LAN use but would fail in air-gapped environments.

6. **Dark theme as default** — The UI defaults to dark mode with a light/dark toggle persisted in localStorage. This reflects the target audience (operators in server rooms/terminals).

7. **IPv4/IPv6/hostname-aware sorting** — The parser classifies client addresses by type and sorts them: hostnames alphabetically, IPv4 numerically, IPv6 lexicographically. This is a thoughtful UX detail for mixed-address environments.

---

## Repository Structure

```
ChronoGuard/
├── ticc-dash.py                    # Flask app + inline HTML/CSS/JS (405 lines)
├── install_ticc_dash.sh            # System installer (systemd + venv + sudoers)
├── uninstall_ticc_dash.sh           # Clean uninstaller (idempotent)
├── README.md                       # Project documentation
├── LICENSE                         # MIT License
├── CODE_OF_CONDUCT.md              # Contributor Covenant v2.1
├── CONTRIBUTING.md                 # Contribution guidelines
├── SECURITY.md                     # Security policy (48h response, 90d disclosure)
├── .gitignore                      # Python/IDE/OS ignores
├── static/img/
│   ├── ticc-dash-logo.png          # PNG logo (brand asset)
│   └── ticc-dash-logo-embedded.svg # SVG logo with embedded base64 PNG
└── .github/
    ├── dependabot.yml              # Dependabot (pip, npm, docker, github-actions)
    ├── workflows/
    │   └── codeql.yml              # CodeQL analysis (Python, JS, TS)
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        ├── feature_request.md
        └── PULL_REQUEST_TEMPLATE.md
```

**Notable absences:**
- No `docs/` directory
- No `tests/` directory
- No `requirements.txt` or `pyproject.toml`
- No `Dockerfile` or `docker-compose.yml`
- No `j1.yaml` (J1 pipeline metadata file)

---

## Notes

- **Repo name vs brand mismatch**: The repository is named `ChronoGuard` but the application is branded as **TICC Dash** ("Time Information of Chrony Clients – Dashboard"). The README explains this: "ChronoGuard (TICC Dash)". This is a documented dual-name, not a naming issue.

- **Fork lineage**: The repo has an `upstream` remote pointing to `anoniemerd/ticc-dash.git`. The initial commit is from the original author. JorahOne forked and migrated the URLs, applied portfolio standardization, and added security auditing.

- **Dependabot config drift**: Dependabot is configured for `npm` and `docker` ecosystems, but there is no `package.json` or `Dockerfile` in the repo. These are template vestiges from the J1 repo template and should be cleaned up.

- **CodeQL config drift**: CodeQL workflow targets `javascript` and `typescript` languages, but there is no standalone JS/TS code — only inline jQuery in the Flask template string. The Python analysis is the only meaningful scan.

- **Security audit in history**: Commit `35c30e7` ("audit(ChronoGuard): sanitize email references") is a positive maturity signal — the repo has undergone at least one security review.

- **No `requirements.txt`**: The install script installs `flask` and `gunicorn` via pip but does not pin versions. This is a supply-chain risk for production deployment.

- **No favicon**: The HTML references `/static/img/favicon.png` but no such file exists in the repo. The browser will 404 on favicon requests.

- **`ticc-dash.org` reference**: The info popup in the dashboard links to `https://ticc-dash.org` — this domain's status is unknown and may not be under JorahOne control.

- **Empty directories**: None found. All directories contain files.
