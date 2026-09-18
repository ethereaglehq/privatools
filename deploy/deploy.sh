#!/usr/bin/env bash
# Production deploy script for the PrivaTools VM.
#
# Pre-conditions (operator responsibility):
#   - You are on the Oracle VM (140.245.15.140), in /opt/privatool, as a user
#     in the `privatool` group with sudo for systemctl/nginx.
#   - node_modules already exists under frontend/. If package.json changed,
#     run `npm ci` MANUALLY before invoking this script — we deliberately
#     skip dep install on the hot path to keep deploys fast.
#   - The Python venv at /opt/privatool/.venv already has requirements.txt
#     (the hashed lock) installed. If requirements.txt changed, run
#     `/opt/privatool/.venv/bin/pip install --require-hashes -r requirements.txt` first.
#
# This script is intentionally minimal-blast-radius: pull, build, restart,
# verify. No DB migrations, no schema changes, no destructive ops.

set -euo pipefail

cd /opt/privatool

echo "[deploy] git fetch + reset to origin/main"
git fetch --prune
git reset --hard origin/main

echo "[deploy] building frontend"
cd frontend
# node_modules persists on VM — DO NOT npm install here.
# If a dep was added (check package.json diff manually), the operator must
# run npm ci first.
npm run build
cd ..

echo "[deploy] restarting backend"
sudo systemctl restart privatool-backend

# Give uvicorn a beat to come up before the health check. Type=notify means
# systemctl restart returns once the unit is "active", but the first worker
# can still be importing routers.
sleep 2

echo "[deploy] reloading nginx"
sudo systemctl reload nginx

echo "[deploy] health check"
curl --fail --max-time 10 http://127.0.0.1:8000/healthz

echo "Deploy complete."
