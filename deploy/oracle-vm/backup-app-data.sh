#!/usr/bin/env bash
# Nightly backup of the accounts database.
#
# This persists the local account mirror and API-key records. Clerk identity
# recovery does not restore these records; legacy native accounts also depend
# on this database. Keep an encrypted off-host copy and rehearse restoration.
#
# The DB lives in the app-data Docker volume, root-owned on the host, inside a
# container with a read-only root filesystem. So rather than reaching into
# /var/lib/docker, take the snapshot from inside the container into /app/temp
# (a writable volume) and copy it out. sqlite3's VACUUM INTO is WAL-safe: it
# takes a consistent snapshot without locking out the live service, which a
# plain cp of a WAL-mode database would not give us.
#
# Install: deploy/oracle-vm/install-backup.sh

set -euo pipefail

# Any running PrivaTools container will do: they all mount the same accounts
# volume. Normally that is the canonical container. While a zero-downtime
# deploy has left the new release on the interim container (the degraded
# state in deploy/README.md), it is that one.
CONTAINER="${CONTAINER:-}"
CANDIDATES="${CANDIDATES:-privatools-privatools-1 privatools-interim-privatools-1}"
# Take the deploy lock so a backup never races a deploy replacing the
# container it reads from. The backup service's start timeout is 10 minutes.
LOCK_FILE="${LOCK_FILE:-/tmp/privatools-auto-deploy.lock}"
LOCK_WAIT="${LOCK_WAIT:-480}"
DB_IN_CONTAINER="${DB_IN_CONTAINER:-/app/data/privatools.db}"
DEST_DIR="${DEST_DIR:-/home/ubuntu/backups/privatools}"
RETAIN_DAYS="${RETAIN_DAYS:-30}"
# Optional Healthchecks.io URL, same pattern as auto-deploy.sh. A backup that
# silently stops running is worse than no backup, because you believe in it.
BACKUP_PING_URL="${BACKUP_PING_URL:-}"

STAMP="$(date -u +%Y%m%d-%H%M%S)"
TMP_IN_CONTAINER="/app/temp/backup-${STAMP}.db"
DEST="${DEST_DIR}/privatools-${STAMP}.db"

log() { printf '[privatools-backup] %s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"; }

ping_backup() {  # ping_backup ok|fail
    [[ -z "$BACKUP_PING_URL" ]] && return 0
    local url="$BACKUP_PING_URL"
    [[ "$1" == "fail" ]] && url="${BACKUP_PING_URL%/}/fail"
    curl --fail --silent --max-time 8 -o /dev/null "$url" || true
}

cleanup() {
    [[ -n "$CONTAINER" ]] && docker exec "$CONTAINER" rm -f "$TMP_IN_CONTAINER" >/dev/null 2>&1
    return 0
}
on_exit() {
    local status="$1" line="$2"
    if [[ "$status" -ne 0 ]]; then
        log "FAILED at line ${line} (exit ${status})"
        ping_backup fail
    fi
    cleanup
}
trap 'on_exit "$?" "$LINENO"' EXIT

running() { [[ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || true)" == true ]]; }

# Root cannot open the deploy user's lock in sticky /tmp (fs.protected_regular);
# a backup run by hand as root proceeds without it.
if [[ "$(id -u)" != 0 ]]; then
    exec 9>>"$LOCK_FILE"
    if ! flock -w "$LOCK_WAIT" 9; then
        log "a deploy has held the deploy lock for ${LOCK_WAIT}s; backing up from whichever container runs"
    fi
else
    log "running as root: not taking the deploy lock"
fi

if [[ -z "$CONTAINER" ]]; then
    for candidate in $CANDIDATES; do
        if running "$candidate"; then
            CONTAINER="$candidate"
            break
        fi
    done
fi
if [[ -z "$CONTAINER" ]] || ! running "$CONTAINER"; then
    log "no PrivaTools container is running (${CONTAINER:-$CANDIDATES}); nothing to back up"
    CONTAINER=""
    ping_backup fail
    exit 1
fi

# Day-1: the release that first ships accounts creates the DB on first signup.
# Absent is not a failure, and must not page anyone.
if ! docker exec "$CONTAINER" test -f "$DB_IN_CONTAINER" 2>/dev/null; then
    log "no accounts DB yet at ${DB_IN_CONTAINER} (nobody has signed up) — nothing to do"
    ping_backup ok
    exit 0
fi

mkdir -p "$DEST_DIR"
chmod 700 "$DEST_DIR"

# VACUUM INTO via the stdlib rather than the sqlite3 CLI, which the slim image
# does not carry. Parameter-bound: the path is ours, but VACUUM INTO takes a
# bind and there is no reason to build the statement by hand.
docker exec "$CONTAINER" python3 -c "
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
con = sqlite3.connect(f'file:{src}?mode=ro', uri=True)
try:
    con.execute('VACUUM INTO ?', (dst,))
finally:
    con.close()
" "$DB_IN_CONTAINER" "$TMP_IN_CONTAINER"

docker cp "${CONTAINER}:${TMP_IN_CONTAINER}" "$DEST"
chmod 600 "$DEST"

# A backup you have never opened is a hope, not a backup. Prove it is a
# readable SQLite file with the users table in it before calling this a success.
USERS=$(python3 -c "
import sqlite3, sys
con = sqlite3.connect(f'file:{sys.argv[1]}?mode=ro', uri=True)
try:
    print(con.execute(\"select count(*) from sqlite_master where type='table' and name='users'\").fetchone()[0])
finally:
    con.close()
" "$DEST" 2>/dev/null || echo 0)

if [[ "$USERS" != "1" ]]; then
    log "VERIFY FAILED: ${DEST} has no users table — treating as a failed backup"
    rm -f "$DEST"
    ping_backup fail
    exit 1
fi

find "$DEST_DIR" -name 'privatools-*.db' -type f -mtime "+${RETAIN_DAYS}" -delete

log "wrote ${DEST} ($(du -h "$DEST" | cut -f1)), verified, $(find "$DEST_DIR" -maxdepth 1 -name 'privatools-*.db' -type f | wc -l | tr -d ' ') kept"
ping_backup ok
