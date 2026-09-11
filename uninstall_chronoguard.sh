#!/usr/bin/env bash
# ==========================================================
#  ChronoGuard Uninstaller
#  - Stops & disables the chronoguard.service unit
#  - Removes the unit file + symlink, reloads systemd
#  - Frees the dashboard port and kills leftover app processes
#  - Removes the chronyc sudoers rule
#  - Removes /opt/chronoguard
#  - Idempotent: safe to re-run
# ==========================================================

set -euo pipefail

APP_DIR="/opt/chronoguard"
SERVICE_NAME="chronoguard.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
WANTS_LINK="/etc/systemd/system/multi-user.target.wants/$SERVICE_NAME"
SUDOERS_FILE="/etc/sudoers.d/chronoguard"
PORT="${PORT:-5000}"

log()  { printf "\n\033[1;34m%s\033[0m\n" "$*"; }
ok()   { printf "\033[1;32m%s\033[0m\n" "$*"; }
run()  { echo "  $*"; eval "$*" >/dev/null 2>&1 || true; }

trap 'echo "❌ Uninstall aborted."; exit 1' ERR

echo "=============================================="
echo "  🧹 Uninstalling ChronoGuard"
echo "=============================================="

# 1) Stop & disable the systemd unit
if systemctl list-unit-files | grep -q "^$SERVICE_NAME"; then
  log "🛑 Stopping and disabling $SERVICE_NAME ..."
  run "sudo systemctl stop '$SERVICE_NAME'"
  run "sudo systemctl disable '$SERVICE_NAME'"
  ok "✅ Service stopped and disabled."
fi

# 2) Remove unit + symlink
log "🗑️  Removing unit file & symlink..."
run "sudo rm -f '$WANTS_LINK'"
run "sudo rm -f '$SERVICE_FILE'"
run "sudo systemctl reset-failed"
run "sudo systemctl daemon-reload"
ok "✅ Unit removed and systemd reloaded."

# 3) Free the dashboard port + kill lingering processes
log "🔌 Freeing TCP port $PORT ..."
run "sudo fuser -k ${PORT}/tcp"
run "sudo pkill -f '$APP_DIR'"
sleep 0.5
run "sudo pkill -9 -f '$APP_DIR'"
ok "✅ Port and processes cleaned."

# 4) Remove the chronyc sudoers rule
log "🔐 Removing sudoers rule..."
run "sudo rm -f '$SUDOERS_FILE'"
run "sudo visudo -c"
ok "✅ Sudoers cleaned and syntax valid."

# 5) Remove application directory
log "📁 Removing $APP_DIR ..."
run "sudo rm -rf '$APP_DIR'"
ok "✅ Application directory removed."

echo
echo "=============================================="
ok "🎉 ChronoGuard uninstalled."
echo "Removed:"
echo "  • Service:          $SERVICE_NAME"
echo "  • App directory:     $APP_DIR"
echo "  • Sudoers rule:     $SUDOERS_FILE"
echo "  • Port $PORT:           freed"
echo
echo "Verify: systemctl status $SERVICE_NAME; ss -lptn 'sport = :$PORT'; ls -la $APP_DIR"
echo "=============================================="
