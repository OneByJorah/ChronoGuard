/* ChronoGuard dashboard UI — single /api/summary polling loop. */
(function () {
    "use strict";

    var REFRESH = (window.CHRONOGUARD && window.CHRONOGUARD.refreshInterval) || 3000;

    /* ---------------- theme ---------------- */
    var THEME_KEY = "chronoguard_theme", OPEN_KEY = "chronoguard_open_rows";
    function applyTheme(theme) {
        $("html").attr("data-bs-theme", theme);
        $("#theme-toggle").prop("checked", theme === "dark");
    }
    applyTheme(localStorage.getItem(THEME_KEY) || "dark");
    $("#theme-toggle").on("change", function () {
        var t = this.checked ? "dark" : "light";
        localStorage.setItem(THEME_KEY, t);
        applyTheme(t);
    });

    /* ---------------- info pop ---------------- */
    var infoBtn = document.getElementById("infoBtn"), infoPop = document.getElementById("infoPop");
    infoBtn.addEventListener("click", function (e) { e.stopPropagation(); infoPop.style.display = infoPop.style.display === "block" ? "none" : "block"; });
    document.addEventListener("click", function (e) { if (!infoPop.contains(e.target) && e.target !== infoBtn) infoPop.style.display = "none"; });

    /* ---------------- helpers ---------------- */
    function toInt(v) { var n = parseInt(v, 10); return isNaN(n) ? 0 : n; }
    function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
    function lastToSeconds(raw) {
        if (!raw) return null; var s = String(raw).trim().toLowerCase();
        if (s === "-" || s === "?" || s === "") return null;
        if (/^\d+$/.test(s)) return parseInt(s, 10);
        var m = s.match(/^(\d+(?:\.\d+)?)\s*([a-z]+)$/i); if (!m) return null;
        var num = parseFloat(m[1]), unit = m[2];
        if (["s", "sec", "secs", "second", "seconds"].indexOf(unit) > -1) return num;
        if (["m", "min", "mins", "minute", "minutes"].indexOf(unit) > -1) return num * 60;
        if (["h", "hr", "hrs", "hour", "hours"].indexOf(unit) > -1) return num * 3600;
        if (["d", "day", "days"].indexOf(unit) > -1) return num * 86400;
        return null;
    }
    function humanLast(raw) {
        var sec = lastToSeconds(raw); if (sec === null) return raw || "-";
        if (sec < 60) return Math.floor(sec) + " sec ago";
        var m = Math.floor(sec / 60); if (m < 60) return m + " min ago";
        var h = Math.floor(m / 60); if (h < 24) return h + " hr ago";
        return Math.floor(h / 24) + " d ago";
    }
    function severity(r) {
        var d = r.severity != null ? r.severity : toInt(r.ntp && r.ntp.drop);
        if (d >= 10) return 2; if (d > 0) return 1; return 0;
    }
    function sevLabel(s) { return s === 2 ? "Critical" : (s === 1 ? "Warning" : "OK"); }
    function iconForAddr(a) { if (/^\d+\.\d+\.\d+\.\d+$/.test(a)) return "🌐"; if (/^[0-9a-fA-F:]+$/.test(a)) return "🔗"; return "💻"; }

    /* ---------------- expand/collapse rows ---------------- */
    function loadOpenSet() { try { return new Set(JSON.parse(localStorage.getItem(OPEN_KEY) || "[]")); } catch (e) { return new Set(); } }
    function saveOpenSet(s) { try { localStorage.setItem(OPEN_KEY, JSON.stringify(Array.from(s))); } catch (e) { } }
    var openSet = loadOpenSet();

    function ipTuple(a) { if (!/^\d+\.\d+\.\d+\.\d+$/.test(a)) return null; return a.split(".").map(function (n) { return parseInt(n, 10); }); }
    function sortRows(rows, mode) {
        var aS = function (r) { return r.addr || ""; };
        if (mode === "ip_order") {
            rows.sort(function (a, b) {
                var A = ipTuple(aS(a)), B = ipTuple(aS(b));
                if (A && B) { for (var i = 0; i < 4; i++) { if (A[i] !== B[i]) return A[i] - B[i]; } return 0; }
                if (A && !B) return -1; if (!A && B) return 1;
                return aS(a).toLowerCase().localeCompare(aS(b).toLowerCase());
            });
        } else if (mode === "drop_desc") { rows.sort(function (a, b) { return toInt(a.ntp && a.ntp.drop) - toInt(b.ntp && b.ntp.drop); }); }
        else if (mode === "last_recent") { rows.sort(function (a, b) { var as = lastToSeconds(a.ntp && a.ntp.last), bs = lastToSeconds(b.ntp && b.ntp.last); if (as === null && bs === null) return 0; if (as === null) return 1; if (bs === null) return -1; return as - bs; }); }
        else if (mode === "severity") { rows.sort(function (a, b) { return severity(b) - severity(a); }); }
        return rows;
    }

    function updateSummary(rows) {
        var ok = 0, w = 0, b = 0;
        rows.forEach(function (r) { var s = severity(r); if (s === 0) ok++; else if (s === 1) w++; else b++; });
        $("#count-ok").text(ok); $("#count-warn").text(w); $("#count-bad").text(b);
    }

    function detailHTML(r) {
        var n = function (o, k) { return (o && o[k]) || "-"; };
        return '<tr class="detail-row" data-detail-for="' + esc(r.addr) + '"><td></td><td colspan="8">' +
            '<div class="metrics">' +
            '<div class="metric"><div class="label">🕙 NTP Packets</div><div class="value">' + esc(n(r.ntp, "count")) + '</div></div>' +
            '<div class="metric"><div class="label">📉 NTP Dropped</div><div class="value">' + esc(n(r.ntp, "drop")) + '</div></div>' +
            '<div class="metric"><div class="label">🕒 NTP Interval</div><div class="value">' + esc(n(r.ntp, "int")) + '</div></div>' +
            '<div class="metric"><div class="label">⏱ NTP IntL</div><div class="value">' + esc(n(r.ntp, "intl")) + '</div></div>' +
            '<div class="metric"><div class="label">📨 Cmd Packets</div><div class="value">' + esc(n(r.cmd, "count")) + '</div></div>' +
            '<div class="metric"><div class="label">👁 Last Seen</div><div class="value">' + esc(humanLast(r.ntp && r.ntp.last)) + '</div></div>' +
            "</div></td></tr>";
    }
    function rowHTML(r) {
        var sev = severity(r), addr = r.addr || "", open = openSet.has(addr), caret = open ? "▲" : "▼";
        return '<tr class="client-row sev-' + sev + '" data-addr="' + esc(addr) + '">' +
            '<td class="caret-cell"><span class="caret">' + caret + '</span></td>' +
            '<td class="addr-cell" title="' + esc(addr) + '">' + iconForAddr(addr) + '&nbsp; ' + esc(addr) + '</td>' +
            '<td class="text-center">' + sevLabel(sev) + "</td>" +
            '<td class="td-num">' + esc(r.ntp && r.ntp.count) + '</td><td class="td-num">' + esc(r.ntp && r.ntp.drop) + '</td>' +
            '<td class="td-num">' + esc(r.ntp && r.ntp.int) + '</td><td class="td-num">' + esc(r.ntp && r.ntp.intl) + '</td>' +
            '<td class="td-num">' + esc(r.cmd && r.cmd.count) + '</td><td class="last-cell">' + esc(humanLast(r.ntp && r.ntp.last)) + "</td></tr>" +
            (open ? detailHTML(r) : "");
    }

    function updateExpandToggleVisual() {
        var total = $("#client-tbody .client-row").length, openCnt = openSet.size;
        $("#expand-toggle").prop("checked", total > 0 && openCnt === total);
    }

    function bindHandlers() {
        $("#client-tbody .client-row").off("click").on("click", function (e) {
            if ($(e.target).closest("a,button,select,input,label").length) return;
            var $row = $(this), addr = $row.data("addr"), isOpen = openSet.has(addr);
            if (isOpen) { $row.find(".caret").text("▼"); $('tr.detail-row[data-detail-for="' + addr + '"]').remove(); openSet.delete(addr); }
            else { $row.find(".caret").text("▲"); $(detailHTML(cache.find(function (r) { return r.addr === addr; }))).insertAfter($row); openSet.add(addr); }
            saveOpenSet(openSet); updateExpandToggleVisual();
        });
        $("#expand-toggle").off("change").on("change", function () {
            if (this.checked) {
                $("#client-tbody .client-row").each(function () {
                    var $r = $(this), a = $r.data("addr");
                    if (!openSet.has(a)) { $r.find(".caret").text("▲"); $(detailHTML(cache.find(function (r) { return r.addr === a; }))).insertAfter($r); openSet.add(a); }
                });
            } else {
                $("#client-tbody .client-row .caret").text("▼");
                $("#client-tbody tr.detail-row").remove();
                openSet = new Set();
            }
            saveOpenSet(openSet); updateExpandToggleVisual();
        });
    }

    var cache = [], lastHash = "";
    function computeHash(rows) { return rows.map(function (r) { return [r.addr, r.ntp && r.ntp.count, r.ntp && r.ntp.drop, r.ntp && r.ntp.int, r.ntp && r.ntp.last, r.cmd && r.cmd.count].join("|"); }).join("~"); }

    function renderClients() {
        var q = $("#search").val().trim().toLowerCase(), mode = $("#sort-select").val();
        var rows = cache.filter(function (r) { return !q || JSON.stringify(r).toLowerCase().indexOf(q) > -1; });
        rows = sortRows(rows, mode); updateSummary(rows);
        $("#client-tbody").html(rows.map(rowHTML).join("") || '<tr><td colspan="9" class="text-center text-dim py-3">No clients found</td></tr>');
        bindHandlers(); updateExpandToggleVisual();
    }

    /* ---------------- other panels ---------------- */
    function showError(elId, msg) { if (msg) { $(elId).removeClass("d-none").text("⚠ " + msg); } else { $(elId).addClass("d-none"); } }

    function renderTracking(t) {
        var d = t.data || {};
        showError("#tracking-error", t.error);
        var set = function (id, v) { $("#" + id).text(v || "--"); };
        set("t-ref", d.reference_id); set("t-systime", d.system_time);
        set("t-last-offset", d.last_offset); set("t-rms-offset", d.rms_offset);
        set("t-frequency", d.frequency); set("t-skew", d.skew);
        set("t-root-delay", d.root_delay); set("t-root-disp", d.root_dispersion);
        set("t-update-int", d.update_interval);
        $("#t-leap").text("Leap: " + (d.leap_status || "--"));
        $("#t-stratum").text("Stratum: " + (d.stratum || "--"));
        var st = d.sync_state || "unknown";
        $("#t-sync").text("State: " + st);
        $("#t-sync").css("color", st === "synced" ? "var(--ok)" : (st.indexOf("leap") > -1 ? "var(--warn)" : "var(--bad)"));
        // sync badge in subinfo
        var badge = $("#sync-badge");
        badge.text("Sync: " + st);
        badge.removeClass("bg-success bg-warning bg-danger");
        badge.addClass(st === "synced" ? "bg-success" : (st.indexOf("leap") > -1 ? "bg-warning" : "bg-danger"));
    }

    var STATE_CLASS = { "*": "st-ok", "+": "st-comb", "-": "st-not", "?": "st-unk", "x": "st-bad", "~": "st-bad" };
    function renderSources(s) {
        showError("#sources-error", s.error);
        if (!s.sources || !s.sources.length) { $("#sources-tbody").html('<tr><td colspan="7" class="text-center text-dim py-3">No sources</td></tr>'); return; }
        var html = s.sources.map(function (r) {
            var cls = STATE_CLASS[r.state] || "st-not";
            return "<tr>" +
                '<td class="text-center"><span class="src-state ' + cls + '">' + esc(r.ms) + "</span></td>" +
                '<td class="addr-cell" title="' + esc(r.name) + '">' + esc(r.name) + "</td>" +
                '<td class="text-center">' + esc(r.state || (r.ms || "").charAt(1)) + "</td>" +
                '<td class="td-num">' + esc(r.stratum) + '</td><td class="td-num">' + esc(r.poll) + "</td>" +
                '<td class="td-num ' + (r.reach_ok ? "reach-ok" : "reach-bad") + '">' + esc(r.reach) + "</td>" +
                '<td class="last-cell">' + esc(r.last_sample) + "</td></tr>";
        }).join("");
        $("#sources-tbody").html(html);
    }

    function renderStats(st) {
        showError("#stats-error", st.error);
        if (!st.sourcestats || !st.sourcestats.length) { $("#stats-tbody").html('<tr><td colspan="8" class="text-center text-dim py-3">No source statistics</td></tr>'); return; }
        var html = st.sourcestats.map(function (r) {
            return "<tr>" +
                '<td class="addr-cell">' + esc(r.name) + "</td>" +
                '<td class="td-num">' + esc(r.np) + '</td><td class="td-num">' + esc(r.nr) + "</td>" +
                '<td class="td-num">' + esc(r.span) + '</td><td class="td-num">' + esc(r.frequency) + "</td>" +
                '<td class="td-num">' + esc(r.freq_skew) + '</td><td class="td-num">' + esc(r.offset) + '</td><td class="td-num">' + esc(r.std_dev) + "</td></tr>";
        }).join("");
        $("#stats-tbody").html(html);
    }

    function renderActivity(a) {
        showError("#activity-error", a.error);
        var d = a.data || {};
        $("#a-online").text(d.online != null ? d.online : "--");
        $("#a-offline").text(d.offline != null ? d.offline : "--");
        $("#a-burst").text(d.burst != null ? d.burst : "--");
        $("#a-unknown").text(d.unknown != null ? d.unknown : "--");
        $("#a-error").text(d.error != null ? d.error : "--");
    }

    function renderEvents(ev) {
        showError("#events-error", ev.error);
        var lines = ev.lines || [];
        $("#events-count").text(lines.length);
        var html = lines.map(function (ln) {
            var m = String(ln).match(/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z)?|\w{3}[ ]+\w{3}[ ]+\d+\s+\d+:\d+:\d+)?(.*)$/);
            var ts = m && m[1] ? m[1] : "";
            return '<div class="ev">' + (ts ? '<span class="ts">' + esc(ts) + "</span>" : "") + esc(m ? m[2] : ln) + "</div>";
        }).join("");
        $("#events-feed").html(html || '<div class="text-dim text-center py-3">No events captured yet</div>');
        autoScrollEvents();
    }

    function autoScrollEvents() {
        if (window.__cgAutoscroll !== false) {
            var feed = document.getElementById("events-feed");
            if (feed) feed.scrollTop = feed.scrollHeight;
        }
    }
    $("#events-scroll-toggle").on("click", function () {
        window.__cgAutoscroll = !window.__cgAutoscroll;
        $(this).text(window.__cgAutoscroll ? "⤓ autoscroll" : "⤒ frozen");
        autoScrollEvents();
    });

    /* ---------------- master refresh ---------------- */
    function refresh() {
        $.getJSON("/api/summary", function (p) {
            var y = window.scrollY;
            var dt = (p.local_time || "").split(", ");
            $("#date-part").text(dt[0] || "--"); $("#time-part").text(dt[1] || "--");
            var rows = (p.clients && p.clients.clients) || [];
            $("#clients-count").text((p.clients && p.clients.count) || 0);
            $("#clients-error").remove();
            var h = computeHash(rows);
            if (h !== lastHash) { cache = rows; renderClients(); lastHash = h; }
            else { updateSummary(cache); }
            renderTracking(p.tracking || {});
            renderSources(p.sources || {});
            renderStats(p.sourcestats || {});
            renderActivity(p.activity || {});
            renderEvents(p.events || {});
            if (window.scrollY !== y) window.scrollTo(0, y);
        }).fail(function () {
            $("#client-tbody").html('<tr><td colspan="9" class="text-center text-danger py-3">Failed to reach server — retrying…</td></tr>');
        });
    }

    $(function () {
        $("#sort-select").on("change", renderClients);
        $("#search").on("input", renderClients);
        refresh();
        setInterval(refresh, REFRESH);
    });
})();
