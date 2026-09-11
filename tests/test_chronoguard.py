"""Parser unit tests + Flask endpoint tests for ChronoGuard.

Runs entirely offline: CHRONYC_PATH points at tests/mock_chronyc and
EVENTS_LOG points at tests/events_sample.log, so no real chrony needed.
"""
import importlib.machinery
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chronoguard  # noqa: E402

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK = os.path.join(TESTS_DIR, "mock_chronyc")
EVENTS_SAMPLE = os.path.join(TESTS_DIR, "events_sample.log")

# Load mock_chronyc by file path (extension-less, so load via SourceFileLoader)
_spec = importlib.util.spec_from_file_location(
    "mock_chronyc", MOCK, loader=importlib.machinery.SourceFileLoader("mock_chronyc", MOCK)
)
mock_chronyc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mock_chronyc)


def setup_function():
    os.environ["CHRONYC_PATH"] = MOCK
    os.environ["CHRONYC_TIMEOUT"] = "5"
    os.environ["EVENTS_LOG"] = EVENTS_SAMPLE


# ----------------------------------------------------------------- parsers


def test_parse_clients_columns_and_severity():
    rows = chronoguard.parse_clients(mock_chronyc.CLIENTS)
    assert len(rows) == 4

    r0 = rows[0]  # 192.168.1.10
    assert r0["addr"] == "192.168.1.10"
    assert r0["ipv4"] is True
    assert r0["ntp"]["count"] == "1234"
    assert r0["ntp"]["drop"] == "1"     # → Warning
    assert r0["ntp"]["int"] == "64"
    assert r0["ntp"]["intl"] == "30"
    assert r0["ntp"]["last"] == "4"
    assert r0["cmd"]["count"] == "10"   # Cmd group correctly separated
    assert r0["cmd"]["drop"] == "0"
    assert r0["severity"] == 1

    r1 = rows[1]  # 192.168.1.11, drop 12 → Critical
    assert r1["severity"] == 2

    r2 = rows[2]  # hostname row
    assert r2["ipv4"] is False and r2["ipv6"] is False
    assert r2["ntp"]["intl"] == "-"

    r3 = rows[3]  # IPv6
    assert r3["ipv6"] is True


def test_parse_tracking():
    t = chronoguard.parse_tracking(mock_chronyc.TRACKING)
    assert t["stratum"] == "3"
    assert t["leap_status"] == "Normal"
    assert "time.cloudflare.com" in t["reference_id"]
    assert t["sync_state"] == "synced"
    assert "+0.000012345" in t["last_offset"]


def test_parse_sources():
    rows = chronoguard.parse_sources(mock_chronyc.SOURCES)
    assert len(rows) == 3
    assert rows[0]["ms"] == "^*"          # synced server
    assert rows[0]["state"] == "*"
    assert rows[0]["name"] == "time.cloudflare.com"
    assert rows[0]["reach"] == "377"
    assert rows[0]["reach_ok"] is True
    assert rows[2]["state"] == "?"        # unreachable
    assert rows[2]["reach_ok"] is False


def test_parse_sourcestats():
    rows = chronoguard.parse_sourcestats(mock_chronyc.SOURCESTATS)
    assert len(rows) == 2
    assert rows[0]["name"] == "time.cloudflare.com"
    assert rows[0]["frequency"]


def test_parse_activity():
    a = chronoguard.parse_activity(mock_chronyc.ACTIVITY)
    assert a["online"] == "2"
    assert a["offline"] == "1"
    assert a["burst"] == "1"
    assert a["unknown"] == "1"
    assert a["error"] == "0"


def test_sync_state_leap_variants():
    t = {"leap_status": "Insert second", "stratum": "4"}
    assert chronoguard._sync_state(t) == "leap pending"
    t = {"leap_status": "Normal", "stratum": "3"}
    assert chronoguard._sync_state(t) == "synced"


# ---------------------------------------------------------------- endpoints


def test_health():
    client = chronoguard.app.test_client()
    data = client.get("/api/health").get_json()
    assert data["status"] == "ok"


def test_clients_endpoint():
    client = chronoguard.app.test_client()
    data = client.get("/api/clients").get_json()
    assert data["count"] == 4
    assert data["error"] is None
    assert data["clients"][0]["addr"] == "192.168.1.10"


def test_summary_endpoint():
    client = chronoguard.app.test_client()
    data = client.get("/api/summary").get_json()

    assert data["clients"]["count"] == 4
    assert data["tracking"]["data"]["sync_state"] == "synced"
    assert len(data["sources"]["sources"]) == 3
    assert len(data["sourcestats"]["sourcestats"]) == 2
    assert data["activity"]["data"]["online"] == "2"
    assert len(data["events"]["lines"]) == 4     # fixture event log
    assert "local_time" in data


def test_data_alias():
    client = chronoguard.app.test_client()
    data = client.get("/data").get_json()
    assert data["count"] == 4


def test_missing_chronyc_returns_error_not_500():
    os.environ["CHRONYC_PATH"] = "/nonexistent/chronyc"
    client = chronoguard.app.test_client()
    resp = client.get("/api/clients")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 0
    assert data["error"]                       # clean error string, not a crash


def test_events_missing_log_falls_back_gracefully():
    os.environ["EVENTS_LOG"] = "/nonexistent/events.log"
    client = chronoguard.app.test_client()
    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "events" in data                    # error surfaced, still 200


def test_index_page_renders():
    client = chronoguard.app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "ChronoGuard" in html
    assert "api/summary" in html
