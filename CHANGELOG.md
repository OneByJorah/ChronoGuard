# Changelog

## [2.0.0] - 2026-09-11
### Revamped
- **Full rebrand to ChronoGuard** — app, installer, uninstaller, systemd unit,
  HTML/branding, assets and docs no longer carry any `ticc-dash` references.
- **Complete dashboard** — added Tracking (sync state, offsets, drift), NTP
  Sources (state/reachability), Source Statistics, Activity, and a live host
  **Events** feed alongside the existing Clients table.
- **Single `/api/summary` endpoint** — one poll updates every panel; individual
  endpoints also exposed.
- **Robust chronyc runner** — plain `chronyc` with `sudo` fallback, 15s timeout,
  per-panel error strings instead of crashes.
- **Offline-first** — Bootstrap 5 + jQuery vendored into `static/vendor/`; no CDN.
- **Real config** — the app now reads `FLASK_HOST`, `FLASK_PORT`, `FLASK_DEBUG`,
  `REFRESH_INTERVAL`, `CHRONYC_PATH`, `CHRONYC_TIMEOUT`, `CHRONY_HOST/PORT`,
  `EVENTS_LOG`, `EVENTS_TAIL`.
- **requirements.txt** pinned; `requirements-dev.txt` for tooling.
- **Systemd unit shipped** in-repo and installed by `install_chronoguard.sh`
  (which also provisions chrony, the venv, and the scoped chronyc sudo rule).
- **Docker fixed** — removed the `network_mode: host` + `ports` conflict, mounts
  the host chrony socket, no sudo dependency in-container.
- **Test suite** — pytest coverage with a mock `chronyc`, plus CI
  (`.github/workflows/ci.yml`) running ruff + pytest.

## [1.0.0] - 2026-07-07
### Added
- Initial release
- Dockerfile with multi-stage build
- docker-compose.yml with healthchecks
- .env.example with placeholder values
- First-run setup wizard / docker-entrypoint.sh (legacy)
- Screenshot documentation
- README with deployment instructions
