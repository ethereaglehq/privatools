#!/usr/bin/env bash
# Point host nginx's PrivaTools upstream at one local port.
#
#   privatools-nginx-upstream set PORT            (the deploy runs it through sudo)
#   privatools-nginx-upstream set PORT --force    (root by hand: skip the readiness check)
#   privatools-nginx-upstream show
#
# Installed as /usr/local/sbin/privatools-nginx-upstream by
# install-auto-deploy.sh. The deploy service runs as ubuntu, and
# /etc/sudoers.d/privatools-deploy lets it run exactly `set 8000` and
# `set 8001` of this file as root, nothing else. That is the only privileged
# step of a deploy.
#
# The switch is atomic from nginx's point of view: the new upstream file is
# written beside the old one and renamed over it, `nginx -t` checks the whole
# configuration, and only then does a graceful reload start new workers on the
# new upstream while the old workers finish their requests. If the test or the
# reload fails, the previous file is put back, so nginx keeps serving (or goes
# back to) the previous upstream and the file always matches what nginx runs.
#
# That promise also holds when the deploy is stopped halfway: from the rename
# to the reload or restore, SIGTERM, SIGINT and SIGHUP are ignored, so
# `systemctl stop` or the unit's start timeout cannot leave a renamed file that
# nginx never loaded. (SIGKILL cannot be ignored; every rollout therefore
# re-applies the file's port before it does anything else.) Concurrent calls
# are serialized, and a port where nothing is ready is refused, so a stray
# switch cannot become an outage.
set -euo pipefail

UPSTREAM_FILE=/etc/nginx/privatools-upstream.conf
UPSTREAM_LOCK=/run/privatools-nginx-upstream.lock
ALLOWED_PORTS="8000 8001"
NGINX_TEST="/usr/sbin/nginx -t -q"
NGINX_RELOAD="/usr/bin/systemctl reload nginx"

# Testing hook for an unprivileged run against a stand-in nginx. Ignored as
# root: through sudo the environment is reset anyway, and root must only ever
# touch the fixed files above.
if [[ "${EUID}" -ne 0 ]]; then
    UPSTREAM_FILE="${PRIVATOOLS_UPSTREAM_FILE:-$UPSTREAM_FILE}"
    UPSTREAM_LOCK="${PRIVATOOLS_UPSTREAM_LOCK:-$UPSTREAM_LOCK}"
    ALLOWED_PORTS="${PRIVATOOLS_ALLOWED_PORTS:-$ALLOWED_PORTS}"
    NGINX_TEST="${PRIVATOOLS_NGINX_TEST:-$NGINX_TEST}"
    NGINX_RELOAD="${PRIVATOOLS_NGINX_RELOAD:-$NGINX_RELOAD}"
fi

log() { printf '[privatools-nginx-upstream] %s\n' "$*" >&2; }

current_port() {
    sed -n 's/^[[:space:]]*server[[:space:]]\{1,\}127\.0\.0\.1:\([0-9]\{1,\}\)[[:space:];].*/\1/p' \
        "$UPSTREAM_FILE" 2>/dev/null | head -n1 || true
}

render() {
    cat <<EOF
# Managed by /usr/local/sbin/privatools-nginx-upstream (deploy/oracle-vm/nginx-upstream.sh).
# The zero-downtime deploy rewrites this file; change it only through that
# helper so every switch is checked with nginx -t before the reload.
upstream privatools_app {
    server 127.0.0.1:$1;
}
EOF
}

target_ready() {  # something on the port answers /readyz with ready
    local body
    body="$(curl --fail --silent --max-time 5 "http://127.0.0.1:$1/readyz" 2>/dev/null)" || return 1
    [[ "$body" == *'"status":"ready"'* || "$body" == *'"status": "ready"'* ]]
}

set_port() {
    local port="$1" force="$2" allowed=false candidate
    for candidate in $ALLOWED_PORTS; do
        [[ "$port" == "$candidate" ]] && allowed=true
    done
    if ! $allowed; then
        log "refusing port '${port}': only ${ALLOWED_PORTS} are PrivaTools upstreams"
        return 2
    fi

    exec 8>>"$UPSTREAM_LOCK"
    if ! flock -w 60 8; then
        log "another switch has held ${UPSTREAM_LOCK} for 60s"
        return 6
    fi
    if ! $force && ! target_ready "$port"; then
        log "refusing: nothing ready answers on 127.0.0.1:${port}/readyz (root can add --force)"
        return 5
    fi

    local directory previous staged had_previous=false status=0
    directory="$(dirname "$UPSTREAM_FILE")"
    previous="${UPSTREAM_FILE}.previous"
    staged="$(mktemp "${directory}/.privatools-upstream.XXXXXX")"
    # shellcheck disable=SC2064  # expand now: the trap must remove this exact file
    trap "rm -f '$staged'" EXIT
    render "$port" > "$staged"
    chmod 0644 "$staged"

    local -a test_command reload_command
    read -ra test_command <<<"$NGINX_TEST"
    read -ra reload_command <<<"$NGINX_RELOAD"
    # From here to the end, finish what was started: see the header.
    trap '' TERM INT HUP
    if [[ -f "$UPSTREAM_FILE" ]]; then
        cp -p "$UPSTREAM_FILE" "$previous"
        had_previous=true
    fi
    mv -f "$staged" "$UPSTREAM_FILE"
    if ! "${test_command[@]}"; then
        status=3
        log "nginx -t rejected the configuration; restored the previous upstream, nothing reloaded"
    elif ! "${reload_command[@]}"; then
        status=4
        log "nginx reload failed; restored the previous upstream file"
    fi
    if (( status != 0 )); then
        if $had_previous; then
            mv -f "$previous" "$UPSTREAM_FILE"
        else
            rm -f "$UPSTREAM_FILE"
        fi
        return "$status"
    fi
    rm -f "$previous"
    log "upstream privatools_app now 127.0.0.1:${port}"
}

case "${1:-}" in
    set)
        if [[ $# -eq 2 ]]; then
            set_port "$2" false
        elif [[ $# -eq 3 && "$3" == --force && "${EUID}" -eq 0 ]]; then
            set_port "$2" true
        else
            log "usage: $0 set PORT [--force (root only)]"
            exit 2
        fi
        ;;
    show)
        port="$(current_port)"
        [[ -n "$port" ]] || { log "no upstream in ${UPSTREAM_FILE}"; exit 1; }
        printf '%s\n' "$port"
        ;;
    *)
        log "usage: $0 set PORT [--force] | show"
        exit 2
        ;;
esac
