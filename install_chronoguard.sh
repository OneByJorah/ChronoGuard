#!/usr/bin/env bash
# ==========================================================
#  ChronoGuard Installer
#  - Installs into /opt/chronoguard
#  - Installs and enables the local Chrony daemon (the NTP server we monitor)
#  - Creates a Python venv and installs from requirements.txt
#  - Adds a NOPASSWD sudo rule so the app can run `chronyc`
#  - Installs a systemd unit (chronoguard.service) and starts it
#  - Idempotent: safe to run again
#
#  Usage:
#    ./install_chronoguard.sh          # from a clone checkout
#    curl -fsSL .../install_chronoguard.sh | sudo bash -s   # remote install
# ==========================================================

set -euo pipefail

APP_NAME="ChronoGuard"
APP_DIR="/opt/chronoguard"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="chronoguard.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
SUDOERS_FILE="/etc/sudoers.d/chronoguard"
GITHUB_REPO="OneByJorah/ChronoGuard"
DEFAULT_PORT="5000"

# Prefer a local checkout if we're running from one.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_APP_FILE="$SCRIPT_DIR/chronoguard.py"

USER_NAME="$(whoami)"

log()  { printf "\n\033[1;34m%s\033[0m\n" "$*"; }
ok()   { printf "\033[1;32m%s\033[0m\n" "$*"; }
warn() { printf "\n\033[1;33m%s\033[0m\n" "$*"; }
die()  { printf "\033[1;31m%s\033[0m\n" "$*" >&2; exit 1; }

trap 'echo; echo "❌ $APP_NAME installation aborted at step: $CURRENT_STEP."; exit 1' ERR

CURRENT_STEP="preparing"

echo "=============================================="
echo "  🚀 Installing $APP_NAME"
echo "=============================================="

command -v sudo >/dev/null 2>&1 || die "sudo is required to install $APP_NAME."
[ "$(id -u)" -eq 0 ] && die "Run this script as a normal user (it uses sudo internally)."

# 1) System dependencies — the monitored Chrony server + Python tooling
CURRENT_STEP="installing system packages"
log "📦 Installing system dependencies (chrony, python3-venv, python3-pip)..."
sudo apt-get update -y
sudo apt-get install -y chrony python3 python3-venv python3-pip curl
ok "✅ System dependencies installed (chronyd is now $(systemctl is-active chronyd 2>/dev/null || echo 'starting'))."

# 2) NOPASSWD sudo rule for chronyc (read-only monitoring commands)
CURRENT_STEP="configuring sudoers"
log "🔐 Configuring NOPASSWD access to /usr/bin/chronyc for: $USER_NAME"
if sudo test -f "$SUDOERS_FILE" && sudo grep -q "chronyc" "$SUDOERS_FILE"; then
  ok "✅ Sudo rule already present."
else
  echo "$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/chronyc" | sudo tee "$SUDOERS_FILE" >/dev/null
  sudo chmod 0440 "$SUDOERS_FILE"
  sudo visudo -cf "$SUDOERS_FILE"
  ok "✅ Sudo rule added and syntax-validated."
fi

# 3) Project directory
CURRENT_STEP="creating project directory"
log "📁 Creating project directory $APP_DIR ..."
sudo mkdir -p "$APP_DIR"
sudo chown -R "$USER_NAME":"$USER_NAME" "$APP_DIR"
ok "✅ Directory ready."

# 4) Application files — local checkout preferred, GitHub tarball fallback
CURRENT_STEP="copying application files"
log "⬇️  Copying application files..."
if [ -f "$LOCAL_APP_FILE" ]; then
  log "   Using local checkout at $SCRIPT_DIR"
  TMP_STAGE="$APP_DIR"
  sudo rsync -a --delete \
      "$SCRIPT_DIR"/chronoguard.py \
      "$SCRIPT_DIR"/requirements.txt \
      "$SCRIPT_DIR"/templates/ \
      "$SCRIPT_DIR"/static/ \
      "$TMP_STAGE/" 2>/dev/null \
    || sudo cp -r "$SCRIPT_DIR"/chronoguard.py "$SCRIPT_DIR"/requirements.txt \
               "$SCRIPT_DIR"/templates "$SCRIPT_DIR"/static "$APP_DIR/"
  sudo chown -R "$USER_NAME":"$USER_NAME" "$APP_DIR"
  ok "✅ Files copied from local checkout."
else
  log "   Downloading latest source from GitHub ($GITHUB_REPO@main)"
  TARBALL="$(mktemp)"
  curl -fsSL "https://codeload.github.com/$GITHUB_REPO/tar.gz/refs/heads/main" -o "$TARBALL"
  sudo tar -xzf "$TARBALL" -C "$APP_DIR" --strip-components=1 --no-same-owner
  rm -f "$TARBALL"
  sudo chown -R "$USER_NAME":"$USER_NAME" "$APP_DIR"
  ok "✅ Files downloaded from GitHub."
fi

# 5) Python venv + dependencies
CURRENT_STEP="creating virtual environment"
log "🐍 Creating Python virtual environment..."
if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
ok "✅ Virtual environment ready (flask + gunicorn installed)."

# 6) systemd service
CURRENT_STEP="installing systemd service"
log "⚙️  Installing systemd service ($SERVICE_NAME)..."
# Locate the unit template — either in this checkout or already staged.
SERVICE_TEMPLATE=""
for candidate in "$SCRIPT_DIR/chronoguard.service" "$APP_DIR/chronoguard.service"; do
  [ -f "$candidate" ] && SERVICE_TEMPLATE="$candidate" && break
done
[ -n "$SERVICE_TEMPLATE" ] || die "Could not locate chronoguard.service template."
sudo cp "$SERVICE_TEMPLATE" "$SERVICE_FILE"
sudo sed -i "s/__CHRONOGUARD_USER__/$USER_NAME/g" "$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# 7) Wait for the dashboard to come up
CURRENT_STEP="waiting for dashboard"
log "⏳ Waiting for the dashboard to answer..."
DASHBOARD_UP=0
for i in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:$DEFAULT_PORT/api/health" >/dev/null 2>&1; then
    ok "✅ Dashboard is up after ${i}s."
    DASHBOARD_UP=1
    break
  fi
  sleep 1
done
# A service that never answers means the install failed — don't report success.
[ "$DASHBOARD_UP" -eq 1 ] || die "Dashboard did not answer on 127.0.0.1:$DEFAULT_PORT after 20s. Inspect 'journalctl -u $SERVICE_NAME -e' (common causes: port in use, gunicorn/venv failure), then re-run this installer."

# 8) Summary
echo
echo "=============================================="
ok "🎉 $APP_NAME installed successfully!"
echo
echo "📍 Directory:     $APP_DIR"
echo "🧩 Service:       $SERVICE_NAME"
echo "🧠 App object:    chronoguard:app"
echo
IP_ADDR="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "🌐 Dashboard:     http://$IP_ADDR:$DEFAULT_PORT/"
echo "🛰  Monitors:      chrony clients · tracking · sources · stats · activity · events"
echo
echo "🔎 Manage:"
echo "  • sudo systemctl status $SERVICE_NAME"
echo "  • sudo journalctl -u $SERVICE_NAME -f"
echo "  • sudo systemctl restart $SERVICE_NAME"
echo "  • ./uninstall_chronoguard.sh  (full removal)"
echo "=============================================="
