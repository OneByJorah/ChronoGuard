#!/usr/bin/env python3
"""
ChronoGuard — live Chrony NTP monitoring dashboard.

A self-contained Flask web app that watches a Chrony server and shows
its clients, tracking state, NTP sources, source statistics, activity
and host events in a real-time dashboard. No database, no CDN, single
command to run:

    python3 chronoguard.py            # dev
    gunicorn --bind 0.0.0.0:5000 chronoguard:app    # production

Everything is configurable through environment variables; see `.env.example`
and the README for the full list.
"""

import os
import shutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template

BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

# --------------------------------------------------------------------------
# Configuration (all overridable via environment; safe defaults)
# --------------------------------------------------------------------------
HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
PORT = int(os.environ.get("FLASK_PORT", "5000"))
DEBUG = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "3000"))
CHRONYC_TIMEOUT = float(os.environ.get("CHRONYC_TIMEOUT", "15"))
CHRONY_HOST = os.environ.get("CHRONY_HOST", "")
CHRONY_PORT = os.environ.get("CHRONY_PORT", "323")
EVENTS_TAIL = int(os.environ.get("EVENTS_TAIL", "100"))

# --------------------------------------------------------------------------
# chronyc runner — tries plain `chronyc` first, then `sudo chronyc`, and
# never raises: a missing binary, denied permission or timeout becomes a
# clean error string on the payload, not a 500.
# --------------------------------------------------------------------------


def _chronyc_connection_args():
    """Extra argv to reach a remote chrony daemon (Docker)."""
    if CHRONY_HOST:
        return ["-h", CHRONY_HOST, "-p", CHRONY_PORT]
    return []


def _run(cmd, timeout=CHRONYC_TIMEOUT):
    """Run a command. Returns (stdout, error); never raises."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            return proc.stdout, err or f"exit code {proc.returncode}"
        return proc.stdout, None
    except FileNotFoundError:
        return None, "command not found"
    except subprocess.TimeoutExpired:
        return None, "timed out"
    except Exception as exc:  # pragma: no cover - defensive
        return None, repr(exc)


def get_chronyc(subcommand):
    """Run `chronyc <subcommand>`, falling back to `sudo chronyc`.

    Returns (stdout_or_None, error_or_None). Plain `chronyc` works against
    the local unix socket without root for read-only commands; `sudo` is a
    fallback when the host restricts it (installer adds a NOPASSWD rule).
    """
    configured = os.environ.get("CHRONYC_PATH", "").strip()
    binary = configured or shutil.which("chronyc") or "/usr/bin/chronyc"
    base = _chronyc_connection_args()
    candidates = [[binary] + base, ["sudo", binary] + base]
    if configured:
        candidates.append(["sudo"] + base)  # configured PATH may not exist under sudo

    tried_sudo = False
    for cmd in candidates:
        if cmd[0] == "sudo" and tried_sudo and not configured:
            continue
        if cmd[0] == "sudo":
            tried_sudo = True
        out, err = _run(cmd + subcommand)
        if err is None:
            return out, None
        low = err.lower()
        if any(t in low for t in ("permission denied", "denied", "not found", "sudo")):
            continue  # not really a chrony error — try the next invocation
        return out, err
    return None, "chronyc unavailable (tried '%s' and 'sudo %s')" % (binary, binary)


# --------------------------------------------------------------------------
# Address helpers
# --------------------------------------------------------------------------


def _is_ipv4(addr):
    try:
        socket.inet_pton(socket.AF_INET, addr)
        return True
    except OSError:
        return False


def _is_ipv6(addr):
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# Parsers — each takes raw `chronyc ...` stdout and returns plain dicts.
# --------------------------------------------------------------------------


def parse_clients(output):
    """`chronyc clients` -> [{addr, ipv4, ipv6, ntp{...}, cmd{...}, severity}]"""
    rows = []
    for raw in output.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith(("Hostname", "==========", "210", "#", "MS")):
            continue
        if "Hostname" in line and "NTP" in line:
            continue
        parts = line.split(None, 1)
        addr = parts[0]
        fields = (parts[1].split() if len(parts) > 1 else []) + [""] * 9
        drop = _to_int(fields[1])
        rows.append(
            {
                "addr": addr,
                "ipv4": _is_ipv4(addr),
                "ipv6": _is_ipv6(addr),
                "ntp": {
                    "count": fields[0],
                    "drop": fields[1],
                    "int": fields[2],
                    "intl": fields[3],
                    "last": fields[4],
                },
                "cmd": {"count": fields[5], "drop": fields[6], "int": fields[7], "last": fields[8]},
                "severity": 2 if drop >= 10 else (1 if drop > 0 else 0),
            }
        )
    return rows


_TRACKING_KEYS = {
    "Reference ID": "reference_id",
    "Stratum": "stratum",
    "Ref time (UTC)": "ref_time",
    "System time": "system_time",
    "Last offset": "last_offset",
    "RMS offset": "rms_offset",
    "Frequency": "frequency",
    "Residual freq": "residual_freq",
    "Skew": "skew",
    "Root delay": "root_delay",
    "Root dispersion": "root_dispersion",
    "Update interval": "update_interval",
    "Leap status": "leap_status",
}


def parse_tracking(output):
    """`chronyc tracking` -> dict of key/values plus a computed sync_state."""
    data = {}
    for raw in output.splitlines():
        line = raw.rstrip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out_key = _TRACKING_KEYS.get(key.strip())
        if out_key:
            data[out_key] = value.strip()
    data["sync_state"] = _sync_state(data)
    return data


def _sync_state(track):
    leap = (track.get("leap_status") or "").lower()
    if "normal" in leap:
        return "synced"
    if "insert" in leap or "delete" in leap:
        return "leap pending"
    if not track.get("stratum"):
        return "not currently synchronised"
    return leap or "unknown"


def parse_sources(output):
    """`chronyc sources -v` -> [{ms, state, name, stratum, poll, reach, last_rx, last_sample, reach_ok}]"""
    rows = []
    for raw in output.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 6:
            continue  # ruler, "210 Number of sources", etc.
        ms = parts[0]
        # Real data rows begin with a mode char (^ server, = peer, # local).
        # Every legend/header line starts with '.', '/', '|' or a word.
        if ms[0] not in ("^", "=", "#"):
            continue
        rows.append(
            {
                "ms": ms,
                "state": ms[1] if len(ms) > 1 else "",
                "name": parts[1],
                "stratum": parts[2],
                "poll": parts[3],
                "reach": parts[4],
                "reach_ok": (parts[4] == "377"),
                "last_rx": parts[5],
                "last_sample": " ".join(parts[6:]),
            }
        )
    return rows


def parse_sourcestats(output):
    """`chronyc sourcestats -v` -> [{name, np, nr, span, frequency, freq_skew, offset, std_dev}]"""
    rows = []
    for raw in output.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 8:
            continue  # ruler, "210 Number of sources", etc.
        if parts[0].lower() in ("name/ip", "ms", "time"):
            continue  # header row
        if not parts[0][0].isalnum():
            continue  # legend lines start with '.', '/', '|', '='
        rows.append(
            {
                "name": parts[0],
                "np": parts[1],
                "nr": parts[2],
                "span": parts[3],
                "frequency": parts[4],
                "freq_skew": parts[5],
                "offset": parts[6],
                "std_dev": parts[7],
            }
        )
    return rows


def parse_activity(output):
    """`chronyc activity` -> {online, offline, burst, unknown, error}"""
    counts = {"online": "--", "offline": "--", "burst": "--", "unknown": "--", "error": "--"}
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "online" in line and "offline" not in line:
            counts["online"] = _num(line)
        elif "offline" in line:
            counts["offline"] = _num(line)
        elif "burst" in line:
            counts["burst"] = _num(line)
        elif "unknown" in line:
            counts["unknown"] = _num(line)
        elif "error" in line:
            counts["error"] = _num(line)
    return counts


def _num(line):
    parts = line.split()
    return parts[0] if parts else "--"


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


# --------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------


def get_clients_data():
    out, err = get_chronyc(["clients"])
    if out is None:
        return [], 0, err or "empty"
    clients = parse_clients(out)
    return clients, len(clients), None


def get_tracking_data():
    out, err = get_chronyc(["tracking"])
    return (parse_tracking(out) if out else {}), err


def get_sources_data():
    out, err = get_chronyc(["sources", "-v"])
    return (parse_sources(out) if out else []), err


def get_sourcestats_data():
    out, err = get_chronyc(["sourcestats", "-v"])
    return (parse_sourcestats(out) if out else []), err


def get_activity_data():
    out, err = get_chronyc(["activity"])
    return (parse_activity(out) if out else {}), err


_LOG_CANDIDATES = [
    "/var/log/chrony/chronyd.log",
    "/var/log/chrony/chrony.log",
    "/var/log/messages",
]


def _tail(path, n):
    try:
        lines = Path(path).read_text(errors="replace").splitlines()
        return lines[-n:] if lines else []
    except OSError:
        return None


def get_events_data():
    """Last EVENTS_TAIL host events: chrony log file first, journalctl fallback."""
    explicit = os.environ.get("EVENTS_LOG", "").strip()
    candidates = [explicit] if explicit else _LOG_CANDIDATES
    for path in candidates:
        lines = _tail(path, EVENTS_TAIL)
        if lines is not None:
            return lines, None
    out, err = _run(
        ["journalctl", "-u", "chronyd", "-n", str(EVENTS_TAIL), "--no-pager", "-o", "short-iso"]
    )
    if err is None and out:
        return out.rstrip().splitlines(), None
    return [], err or "no chrony event log found (looked in %s)" % ", ".join(candidates)


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.route("/")
def dashboard():
    return render_template("index.html", refresh_interval=REFRESH_INTERVAL)


@app.route("/api/clients")
def api_clients():
    clients, count, err = get_clients_data()
    return jsonify({"clients": clients, "count": count, "error": err,
                    "local_time": _local_time()})


@app.route("/api/tracking")
def api_tracking():
    data, err = get_tracking_data()
    return jsonify({"tracking": data, "error": err, "local_time": _local_time()})


@app.route("/api/sources")
def api_sources():
    sources, err = get_sources_data()
    return jsonify({"sources": sources, "count": len(sources), "error": err,
                    "local_time": _local_time()})


@app.route("/api/sourcestats")
def api_sourcestats():
    stats, err = get_sourcestats_data()
    return jsonify({"sourcestats": stats, "count": len(stats), "error": err,
                    "local_time": _local_time()})


@app.route("/api/activity")
def api_activity():
    data, err = get_activity_data()
    return jsonify({"activity": data, "error": err, "local_time": _local_time()})


@app.route("/api/events")
def api_events():
    lines, err = get_events_data()
    return jsonify({"events": lines, "count": len(lines), "error": err,
                    "local_time": _local_time()})


@app.route("/api/summary")
def api_summary():
    """One combined payload for the dashboard's single polling loop."""
    clients, count, err_c = get_clients_data()
    tracking, err_t = get_tracking_data()
    sources, err_s = get_sources_data()
    stats, err_ss = get_sourcestats_data()
    activity, err_a = get_activity_data()
    events, err_e = get_events_data()
    return jsonify(
        {
            "clients": {"clients": clients, "count": count, "error": err_c},
            "tracking": {"data": tracking, "error": err_t},
            "sources": {"sources": sources, "count": len(sources), "error": err_s},
            "sourcestats": {"sourcestats": stats, "count": len(stats), "error": err_ss},
            "activity": {"data": activity, "error": err_a},
            "events": {"lines": events, "count": len(events), "error": err_e},
            "local_time": _local_time(),
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


@app.route("/data")
def data_alias():
    """Backwards-compatible alias for /api/clients."""
    return api_clients()


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "service": "chronoguard"})


def _local_time():
    return datetime.now().strftime("%d-%m-%Y, %H:%M:%S")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"ChronoGuard starting on {HOST}:{PORT} (debug={DEBUG})")
    app.run(host=HOST, port=PORT, debug=DEBUG)
