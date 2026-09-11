# ChronoGuard — Fixes & Enhancements Log

## v2.0.0 (2026-09-11) — full revamp

### Naming consistency
- Everything renamed from the upstream `ticc-dash` to **ChronoGuard**:
  `chronoguard.py`, `install_chronoguard.sh`, `uninstall_chronoguard.sh`,
  `chronoguard.service`, `/opt/chronoguard`, `static/img/chronoguard-logo.svg`.
- Old assets and scripts removed; no `ticc-dash` references remain.

### Bug fixes ("it just works")
- **README now matches reality** — quick start pointed at a nonexistent
  `app.py`/`requirements.txt`; project structure, endpoints and config tables
  described files that didn't exist. All documented against the actual tree.
- **`requirements.txt`** created (pinned Flask + Gunicorn); install no longer
  relies on ad-hoc `pip install flask gunicorn`.
- **`docker-compose.yml`** had `network_mode: host` *and* `ports` (conflict) and
  passed env vars the app ignored. Now uses bridge networking + port mapping
  and mounts the host chrony socket.
- **Docker no longer needs sudo** — the app called `sudo chronyc` which cannot
  work in a container. It now calls plain `chronyc` against the mounted socket.
- **`app.run(debug=True)`** removed as the default; `FLASK_DEBUG` is off by
  default, never enabled in Docker.
- **Favicon 404** — logo is now an SVG and doubles as the favicon.
- **`chronyc clients` parsing fixed** — the old field indexing split the 9 real
  columns incorrectly and mangled NTP vs command statistics.
- **Resilience** — missing/erroring `chronyc` returns a clean `error` field per
  panel, not a 500; 15s timeout for the (CPU-only) host.

### Features
- Full dashboard: Clients, Tracking, Sources, Source Stats, Activity, Events.
- Vendored Bootstrap 5 + jQuery — dashboard is fully offline/CDN-free.
- Real env-var configuration (see `README.md` / `.env.example`).
- Pytest suite + mock `chronyc`; CI workflow runs ruff + pytest.
- Auto-detecting events feed with `journalctl` fallback.

### Packaging
- `.dockerignore`, `requirements-dev.txt`, `chronoguard.service` template added.
