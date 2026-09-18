#!/usr/bin/env bash
# Install the GitHub polling auto-deploy timer and its zero-downtime rollout
# on the Oracle VM.
#
#   sudo bash deploy/oracle-vm/install-auto-deploy.sh           install and validate only
#   sudo bash deploy/oracle-vm/install-auto-deploy.sh --start   also enable the timer and deploy now
#
# Installs:
#   /usr/local/bin/privatools-auto-deploy      auto-deploy.sh: choose and verify the release
#   /usr/local/bin/privatools-rollout          rollout.sh: replace it with zero downtime
#   /usr/local/sbin/privatools-nginx-upstream  nginx-upstream.sh: the only root step
#   /etc/sudoers.d/privatools-deploy           lets ubuntu run exactly that helper with 8000 or 8001
#   /etc/nginx/privatools-upstream.conf        only when absent: port 8000, where traffic already goes
#   the privatools-auto-deploy service and timer units
#
# It never edits the nginx site, reloads nginx, touches the backup timer or
# starts a deploy unless --start is given. The installed copies are what run:
# updating the checkout alone changes nothing, and a deploy does not reinstall
# them (deploy/README.md, "Zero-downtime deploys").

set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/ubuntu/privatools}"
REPO_URL="${REPO_URL:-https://github.com/ethereaglehq/privatools.git}"
APP_USER="${APP_USER:-ubuntu}"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run with sudo: sudo bash deploy/oracle-vm/install-auto-deploy.sh [--start]" >&2
    exit 1
fi

start=false
case "${1:-}" in
    "") ;;
    --start) start=true ;;
    *) echo "usage: $0 [--start]" >&2; exit 2 ;;
esac

if [[ ! -d "$REPO_DIR/.git" ]]; then
    echo "Missing git checkout at $REPO_DIR" >&2
    exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# A malformed file in sudoers.d can break sudo for everyone: check it first.
visudo -cf "$script_dir/privatools-deploy.sudoers"

install -m 0755 "$script_dir/auto-deploy.sh" /usr/local/bin/privatools-auto-deploy
install -m 0755 "$script_dir/rollout.sh" /usr/local/bin/privatools-rollout
install -o root -g root -m 0755 "$script_dir/nginx-upstream.sh" /usr/local/sbin/privatools-nginx-upstream
install -o root -g root -m 0440 "$script_dir/privatools-deploy.sudoers" /etc/sudoers.d/privatools-deploy
visudo -c >/dev/null
if [[ ! -e /etc/nginx/privatools-upstream.conf ]]; then
    install -o root -g root -m 0644 "$script_dir/privatools-upstream.conf" /etc/nginx/privatools-upstream.conf
fi
install -m 0644 "$script_dir/privatools-auto-deploy.service" /etc/systemd/system/privatools-auto-deploy.service
install -m 0644 "$script_dir/privatools-auto-deploy.timer" /etc/systemd/system/privatools-auto-deploy.timer

sudo -u "$APP_USER" git -C "$REPO_DIR" remote set-url origin "$REPO_URL"
sudo -u "$APP_USER" git -C "$REPO_DIR" fetch --prune origin "+refs/heads/main:refs/remotes/origin/main"

systemctl daemon-reload
if $start; then
    systemctl enable --now privatools-auto-deploy.timer
    systemctl start privatools-auto-deploy.service
fi

echo "installed; upstream now $(/usr/local/sbin/privatools-nginx-upstream show)"
systemctl status privatools-auto-deploy.timer --no-pager --lines=20 || true
systemctl status privatools-auto-deploy.service --no-pager --lines=40 || true
