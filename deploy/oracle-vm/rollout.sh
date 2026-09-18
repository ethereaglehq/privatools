#!/usr/bin/env bash
# Replace the running PrivaTools release without taking the site offline.
#
#   privatools-rollout IMAGE BUILD_SHA   run IMAGE, which must report BUILD_SHA
#   privatools-rollout --rollback        run the release the last rollout replaced
#
# Installed as /usr/local/bin/privatools-rollout. auto-deploy.sh calls it with
# the cosign-verified digest of a release tag; deploy.sh calls it with a local
# build. It never pulls, builds or verifies anything itself.
#
# Run it as the deploy user, never as root. The timer does; by hand:
#   sudo runuser -u ubuntu -g ubuntu -G docker -- privatools-rollout ...
# It refuses root, because root cannot open the deploy lock the timer owns in
# sticky /tmp (fs.protected_regular) and would leave state the timer cannot use.
#
# The steady state is one container, privatools-privatools-1 on
# 127.0.0.1:8000, exactly as before; the backup, the manual commands in
# deploy/README.md and the CI image probe all rely on that. A rollout passes
# traffic through a temporary second compose project, privatools-interim, on
# 127.0.0.1:8001:
#
#   0. Make nginx serve what its upstream file names (a killed run can leave
#      the file renamed but not reloaded) and retire any leftover interim.
#   1. Start the interim container on the new image beside the live one. Wait
#      for /readyz to report BUILD_SHA and for the real-page probe
#      (scripts/ci/probe-image.py --running) to pass. Hand the async job queue
#      over: the old supervisor finishes its current job, the new one takes
#      the lock and must keep it, without a container restart, for a soak
#      period. Only then switch host nginx to 8001 (nginx -t, graceful reload,
#      and proof that the reload happened) and check through nginx that the
#      new build answers. Otherwise remove the interim and stop: the live
#      release never stopped serving.
#   2. Let the old container finish its in-flight requests, including those
#      nginx's retiring workers still pass to it. A container that still
#      receives requests after those workers exited is never removed.
#   3. Recreate the canonical container on the new image, gate it the same
#      way, hand the queue to it, switch nginx back to 8000, drain the interim
#      and remove it.
#
# The replaced release is recorded before anything destroys it; --rollback
# runs it again the same way, also from the degraded state below.
#
# Exit status:
#   0  BUILD_SHA serves from the canonical container
#   1  the new release was rejected (not ready, broken pages, or its job
#      supervisor could not hold the queue); the previous release serves
#   2  nothing was started, or a host problem undid the attempt (nginx, Docker,
#      memory, a job that would not finish); the previous release serves;
#      retry later
#   3  degraded: the new release serves from the interim container
#   4  nginx could not be brought to a verified state, or a container that
#      still receives requests had to be kept; act now
# -E: the ERR trap below also reports failures inside functions.
set -Eeuo pipefail

REPO_DIR="${REPO_DIR:-/home/ubuntu/privatools}"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-privatools}"
INTERIM_PROJECT="${INTERIM_PROJECT:-${COMPOSE_PROJECT}-interim}"
SERVICE=privatools
CANONICAL_PORT="${CANONICAL_PORT:-8000}"
INTERIM_PORT="${INTERIM_PORT:-8001}"
# Host nginx includes this file; only the root helper writes it.
UPSTREAM_FILE="${UPSTREAM_FILE:-/etc/nginx/privatools-upstream.conf}"
# The site must proxy through that upstream, or a switch would change nothing.
NGINX_SITE="${NGINX_SITE:-/etc/nginx/sites-enabled/privatools}"
NGINX_SWITCH="${NGINX_SWITCH:-sudo -n /usr/local/sbin/privatools-nginx-upstream set}"
NGINX_PID_FILE="${NGINX_PID_FILE:-/run/nginx.pid}"
# Checked through nginx after each switch: the public path, not the port.
PUBLIC_READY_URL="${PUBLIC_READY_URL:-https://privatools.me/readyz}"
PUBLIC_RESOLVE="${PUBLIC_RESOLVE:-privatools.me:443:127.0.0.1}"
PROBE_SCRIPT="${PROBE_SCRIPT:-${REPO_DIR}/scripts/ci/probe-image.py}"
PYTHON="${PYTHON:-python3}"
# The job supervisor's status, inside a container; standard library only, so
# polling it costs about 0.06 CPU-s instead of the app's 1 s of imports.
STATUS_MODULE="${STATUS_MODULE:-backend.app.job_handover}"
# Uvicorn respawns workers that die at import, so a broken release never
# exits: readiness needs a deadline, and a crash loop is caught early.
READY_TIMEOUT="${READY_TIMEOUT:-180}"
# A reload must visibly retire nginx's previous worker generation this fast.
SWITCH_VERIFY="${SWITCH_VERIFY:-10}"
# nginx passes a request to its upstream only after buffering the whole body,
# so an upload that began before a switch can still reach the old container
# from a retiring nginx worker. Keep the old container until that nginx
# generation has exited, or DRAIN_MAX seconds (nginx's 300 s timeouts), and
# then until no request has been in flight on it for DRAIN_QUIET seconds.
# Once that generation has exited, nothing nginx runs should reach it: a
# connection that lasts DRAIN_ROUTED_GRACE seconds means nginx still routes
# there, and the container is kept (exit 4).
DRAIN_MAX="${DRAIN_MAX:-300}"
DRAIN_EXTRA="${DRAIN_EXTRA:-120}"
DRAIN_QUIET="${DRAIN_QUIET:-3}"
DRAIN_ROUTED_GRACE="${DRAIN_ROUTED_GRACE:-5}"
# A running async job may take up to runtime_seconds (300 s) to finish.
HANDOVER_MAX="${HANDOVER_MAX:-360}"
# The new supervisor must take the queue within HANDOVER_CONFIRM seconds and
# keep it, without its container restarting, for HANDOVER_SOAK seconds.
HANDOVER_CONFIRM="${HANDOVER_CONFIRM:-30}"
HANDOVER_SOAK="${HANDOVER_SOAK:-5}"
# Only for a replaced release older than the drainable supervisor (the first
# deploy after the cut-over): how long to wait for a fully idle queue.
HANDOVER_IDLE_WAIT="${HANDOVER_IDLE_WAIT:-60}"
# Two containers share the VM during the overlap. Refuse to start the second
# one unless this much memory is available (see deploy/README.md).
MIN_AVAILABLE_MB="${MIN_AVAILABLE_MB:-1536}"
MEMINFO="${MEMINFO:-/proc/meminfo}"
STATE_DIR="${STATE_DIR:-$REPO_DIR}"
PREVIOUS_FILE="${PREVIOUS_FILE:-${STATE_DIR}/.privatools-deploy.previous}"
RESUME_FILE="${RESUME_FILE:-${STATE_DIR}/.privatools-deploy.resume}"
RESUME_BACKOFF="${RESUME_BACKOFF:-600}"
LOCK_FILE="${LOCK_FILE:-/tmp/privatools-auto-deploy.lock}"
POLL="${POLL:-1}"

COMPOSE_FILE_PATH="${REPO_DIR}/docker-compose.yml"
INTERIM_FILE_PATH="${REPO_DIR}/deploy/oracle-vm/compose.interim.yml"

data_volume=""
temp_volume=""
jobs_enabled=false
retired_workers=()

log() {
    printf '[privatools-rollout] %s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

# Invoked indirectly by the ERR trap below. The main phases run in `||`
# context, where bash suspends errexit and this trap, so every step there
# checks its own result.
# shellcheck disable=SC2329
on_error() {
    log "unexpected failure at line $2 (exit $1); the next run reconciles from the nginx upstream"
}
trap 'on_error "$?" "$LINENO"' ERR

now() { date +%s; }

mark_resume() {  # the canonical container failed: back off before retrying it
    touch "$RESUME_FILE" 2>/dev/null || log "WARNING: cannot write ${RESUME_FILE}; the next run will not back off"
}

canonical_compose() {
    PRIVATOOLS_HOST_PORT="$CANONICAL_PORT" \
        docker compose -p "$COMPOSE_PROJECT" -f "$COMPOSE_FILE_PATH" "$@"
}

interim_compose() {
    PRIVATOOLS_HOST_PORT="$INTERIM_PORT" PRIVATOOLS_DATA_VOLUME="$data_volume" \
        PRIVATOOLS_TEMP_VOLUME="$temp_volume" \
        docker compose -p "$INTERIM_PROJECT" -f "$COMPOSE_FILE_PATH" -f "$INTERIM_FILE_PATH" "$@"
}

container_of() {  # container_of PROJECT -> its service container, running or not
    docker ps -aq --filter "label=com.docker.compose.project=$1" \
        --filter "label=com.docker.compose.service=${SERVICE}" \
        --filter "label=com.docker.compose.oneoff=False" 2>/dev/null | head -n1 || true
}

image_of() { docker inspect -f '{{.Image}}' "$1" 2>/dev/null || true; }

sha_of() {  # the PRIVATOOLS_BUILD_SHA a container was started with; nothing else is read
    docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$1" 2>/dev/null \
        | sed -n 's/^PRIVATOOLS_BUILD_SHA=//p' | head -n1 || true
}

mount_of() {  # mount_of CONTAINER DESTINATION -> named volume mounted there
    docker inspect -f "{{range .Mounts}}{{if eq .Destination \"$2\"}}{{.Name}}{{end}}{{end}}" "$1" 2>/dev/null || true
}

image_id() { docker image inspect -f '{{.Id}}' "$1" 2>/dev/null || true; }

is_running() { [[ -n "${1:-}" && "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || true)" == true ]]; }

restarts_of() { docker inspect -f '{{.RestartCount}}' "$1" 2>/dev/null || echo gone; }

readyz_sha() {  # readyz_sha URL [CURL_ARGS...] -> build_sha when the body says ready
    local body
    body="$(curl --fail --silent --max-time 5 "$@" 2>/dev/null)" || return 1
    [[ "$body" == *'"status":"ready"'* || "$body" == *'"status": "ready"'* ]] || return 1
    sed -n 's/.*"build_sha": *"\([^"]*\)".*/\1/p' <<<"$body"
}

ready_sha() { readyz_sha "http://127.0.0.1:$1/readyz" || true; }

serves() {  # serves PORT SHA
    [[ -n "$2" && "$(ready_sha "$1")" == "$2" ]]
}

public_serves() {  # public_serves SHA: nginx forwards to a ready release reporting SHA
    local -a resolve=()
    local attempt
    [[ -n "$PUBLIC_RESOLVE" ]] && resolve=(--resolve "$PUBLIC_RESOLVE")
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        if [[ "$(readyz_sha "$PUBLIC_READY_URL" "${resolve[@]}" || true)" == "$1" ]]; then
            return 0
        fi
        sleep "$POLL"
    done
    log "nginx does not forward to a ready ${1:0:12} (${PUBLIC_READY_URL}, attempt ${attempt})"
    return 1
}

live_port() {
    sed -n 's/^[[:space:]]*server[[:space:]]\{1,\}127\.0\.0\.1:\([0-9]\{1,\}\)[[:space:];].*/\1/p' \
        "$UPSTREAM_FILE" 2>/dev/null | head -n1 || true
}

wait_ready() {  # wait_ready CONTAINER PORT SHA
    local container="$1" port="$2" sha="$3" deadline status restarts
    deadline=$(( $(now) + READY_TIMEOUT ))
    while (( $(now) < deadline )); do
        serves "$port" "$sha" && return 0
        read -r status restarts <<<"$(docker inspect -f '{{.State.Status}} {{.RestartCount}}' "$container" 2>/dev/null || echo missing 0)"
        if [[ "$status" == exited || "$status" == dead || "$status" == missing ]] || (( restarts > 0 )); then
            log "container ${container:0:12} gave up before it was ready (${status}, ${restarts} restarts)"
            return 1
        fi
        sleep "$POLL"
    done
    log "container ${container:0:12} did not report ${sha:0:12} ready within ${READY_TIMEOUT}s"
    return 1
}

page_probe() {  # page_probe CONTAINER PORT SHA: real pages, not only /readyz
    log "probing real pages on 127.0.0.1:$2"
    "$PYTHON" "$PROBE_SCRIPT" --running "$1" --url "http://127.0.0.1:$2" --sha "$3" 2>&1 | sed 's/^/    /'
}

show_logs() {
    docker logs --tail 60 "$1" 2>&1 | sed 's/^/    /' || true
}

# ── nginx ────────────────────────────────────────────────────────────────────

nginx_workers() {  # PIDs of nginx's current worker generation (not those already retiring)
    local master
    master="$(cat "$NGINX_PID_FILE" 2>/dev/null || true)"
    [[ "$master" =~ ^[0-9]+$ ]] || return 0
    ps -o pid=,args= --ppid "$master" 2>/dev/null \
        | awk 'NF == 4 && $2 == "nginx:" && $3 == "worker" && $4 == "process" { print $1 }' || true
}

nginx_retiring() {  # PIDs of nginx workers from any earlier generation, still shutting down
    local master
    master="$(cat "$NGINX_PID_FILE" 2>/dev/null || true)"
    [[ "$master" =~ ^[0-9]+$ ]] || return 0
    ps -o pid=,args= --ppid "$master" 2>/dev/null | awk '/nginx: worker process is shutting down/ { print $1 }' || true
}

alive_workers() {  # alive_workers PID...: those still nginx workers (a reused PID is not)
    local pid
    for pid in "$@"; do
        [[ "$(ps -o args= -p "$pid" 2>/dev/null || true)" == "nginx: worker process"* ]] && printf '%s\n' "$pid"
    done
    return 0
}

generation_retiring() {  # PID...: every one has exited or is shutting down
    local pid
    for pid in "$@"; do
        [[ "$(ps -o args= -p "$pid" 2>/dev/null || true)" == "nginx: worker process" ]] && return 1
    done
    return 0
}

switch_to() {  # switch_to PORT: the helper, then proof that nginx reloaded
    local -a command
    local deadline
    read -ra command <<<"$NGINX_SWITCH"
    mapfile -t retired_workers < <(nginx_workers)
    log "switching nginx to 127.0.0.1:$1"
    if ! "${command[@]}" "$1"; then
        log "nginx switch to $1 failed; the helper kept the previous upstream"
        return 1
    fi
    if [[ "$(live_port)" != "$1" ]]; then
        log "the upstream file does not name port $1 after the switch"
        return 1
    fi
    if (( ${#retired_workers[@]} == 0 )); then
        log "note: nginx's worker processes are not visible (${NGINX_PID_FILE}); the reload is unverified"
        return 0
    fi
    deadline=$(( $(now) + SWITCH_VERIFY ))
    until generation_retiring "${retired_workers[@]}"; do
        if (( $(now) >= deadline )); then
            log "nginx did not reload: its workers from before the switch still take requests"
            return 1
        fi
        sleep "$POLL"
    done
}

reconcile_nginx() {  # reconcile_nginx LIVE: make nginx really serve a ready upstream; 0, 2 or 4
    local live="$1" other
    if [[ "$live" == "$CANONICAL_PORT" ]]; then other="$INTERIM_PORT"; else other="$CANONICAL_PORT"; fi
    if [[ -n "$(ready_sha "$live")" ]]; then
        # Re-applied on every run: a run killed between the helper's rename and
        # its reload leaves the file naming a port nginx does not serve.
        switch_to "$live" && return 0
        # The helper put the old file back, or nginx did not reload.
        log "could not re-apply the upstream (${live}); nginx may not match its file; retry later"
        return 2
    fi
    if [[ -n "$(ready_sha "$other")" ]]; then
        log "the upstream names ${live}, where nothing is ready; switching to ${other}, which serves"
        switch_to "$other" && return 0
        log "CRITICAL: could not switch nginx to ${other}, the only port that serves"
        return 4
    fi
    log "CRITICAL: nothing is ready on ${live} or ${other}; continuing, since a ready release would fix this"
    retired_workers=()
    return 0
}

# ── draining ─────────────────────────────────────────────────────────────────

connections() {  # client connections open to the app in CONTAINER (loopback, i.e. its own healthcheck, excluded)
    { docker exec "$1" cat /proc/net/tcp /proc/net/tcp6 2>/dev/null || true; } | awk '
        $4 == "01" {
            split($2, here, ":"); split($3, peer, ":")
            if (here[2] == "1F40" && peer[1] != "0100007F" \
                && peer[1] != "00000000000000000000000001000000" \
                && peer[1] != "0000000000000000FFFF00000100007F") n++
        }
        END { print n + 0 }'
}

drain_http() {  # drain_http CONTAINER RETIRED_NGINX_PID...: 0 drained, 4 nginx still routes to it
    local container="$1" tracked start elapsed busy old quiet_since="" routed_since=""
    shift
    if (( $# > 0 )); then
        # Also wait for older generations still shutting down, such as those a
        # killed run retired: their late requests are not misrouting.
        local -a lingering
        mapfile -t lingering < <(nginx_retiring)
        set -- "$@" "${lingering[@]}"
    fi
    tracked=$#
    start="$(now)"
    while :; do
        elapsed=$(( $(now) - start ))
        # Workers first: a connection counted after they were seen gone is
        # not one of theirs.
        old="$(alive_workers "$@" | wc -l)"
        busy="$(connections "$container")"
        if (( busy == 0 )); then
            quiet_since="${quiet_since:-$(now)}"
            routed_since=""
        else
            quiet_since=""
        fi
        if (( tracked > 0 && old == 0 )); then
            # The retired generation has exited, and the reload was verified:
            # nothing nginx still runs should reach this container.
            if (( busy > 0 )); then
                routed_since="${routed_since:-$(now)}"
                if (( $(now) - routed_since >= DRAIN_ROUTED_GRACE )); then
                    log "CRITICAL: ${container:0:12} still receives requests after nginx's retired workers exited, so nginx still routes to it; keeping it"
                    return 4
                fi
            elif (( $(now) - quiet_since >= DRAIN_QUIET )); then
                log "${container:0:12} drained after ${elapsed}s"
                return 0
            fi
        elif [[ -n "$quiet_since" ]] && (( $(now) - quiet_since >= DRAIN_QUIET )) \
            && (( tracked == 0 || elapsed >= DRAIN_MAX )); then
            log "${container:0:12} drained after ${elapsed}s (${old} retired nginx workers still open elsewhere)"
            return 0
        elif (( elapsed >= DRAIN_MAX + DRAIN_EXTRA )); then
            if (( tracked > 0 )); then
                log "WARNING: ${busy} requests of nginx's retired workers still open on ${container:0:12} after ${elapsed}s; retiring it anyway"
                return 0
            fi
            log "CRITICAL: ${container:0:12} still receives requests after ${elapsed}s and nginx's workers cannot be seen; keeping it"
            return 4
        fi
        sleep "$POLL"
    done
}

# ── async job handover (see backend/app/api_v1/jobs/worker.py) ────────────────

worker_view() {  # CONTAINER -> "ENABLED ROLE PASSIVE ALIVE RUNNING QUEUED"; fails for older releases
    local json
    [[ -n "${1:-}" ]] || return 1
    json="$(docker exec "$1" python -m "$STATUS_MODULE" --status 2>/dev/null)" || return 1
    "$PYTHON" -c '
import json, sys
state = json.loads(sys.argv[1])
local = state.get("local") or {}
count = lambda name: -1 if state.get(name) is None else state[name]
flag = lambda value: "true" if value else "false"
print(flag(state.get("enabled")), local.get("role") or "none", flag(local.get("passive")),
      flag(local.get("alive")), count("running_jobs"), count("queued_jobs"))
' "$json" 2>/dev/null
}

detect_jobs() {  # detect_jobs CONTAINER...: are async jobs enabled in this deployment?
    local container view
    for container in "$@"; do
        if view="$(worker_view "$container")"; then
            [[ "${view%% *}" == true ]] && jobs_enabled=true || jobs_enabled=false
            return 0
        fi
    done
    jobs_enabled=false
}

signal_if() {  # signal_if CONTAINER SIGNAL drainable|passive: 0 when sent
    local view role passive alive
    view="$(worker_view "$1")" || return 1
    read -r _ role passive alive _ _ <<<"$view"
    # A supervisor writes its state (alive) only after installing its handlers.
    [[ "$alive" == true ]] || return 1
    case "$3" in
        drainable) [[ "$role" == active || "$role" == draining ]] || return 1 ;;
        # A supervisor still finishing its job after SIGUSR1 reports
        # "draining"; resuming it then keeps the lock where it is.
        passive) [[ "$passive" == true || "$role" == draining ]] || return 1 ;;
    esac
    docker kill --signal "$2" "$1" >/dev/null 2>&1
}

wait_released() {  # wait_released FROM: until its supervisor holds no job lock
    local deadline view role
    deadline=$(( $(now) + HANDOVER_MAX ))
    while (( $(now) < deadline )); do
        view="$(worker_view "$1")" || return 0      # stopped or gone: holds nothing
        read -r _ role _ _ _ _ <<<"$view"
        [[ "$role" != active && "$role" != draining ]] && return 0
        sleep "$POLL"
    done
    return 1
}

confirm_active() {  # confirm_active TO BASELINE_RESTARTS: holds the queue, keeps it, no restart
    local to="$1" baseline="$2" deadline soak_until="" view role alive
    deadline=$(( $(now) + HANDOVER_CONFIRM ))
    while :; do
        if ! is_running "$to" || [[ "$(restarts_of "$to")" != "$baseline" ]]; then
            log "the job supervisor of ${to:0:12} failed: its container restarted or stopped"
            return 1
        fi
        view="$(worker_view "$to")" || view="false none false false -1 -1"
        read -r _ role _ alive _ _ <<<"$view"
        if [[ "$role" == active && "$alive" == true ]]; then
            soak_until="${soak_until:-$(( $(now) + HANDOVER_SOAK ))}"
            if (( $(now) >= soak_until )); then
                log "the job supervisor in ${to:0:12} holds the queue"
                return 0
            fi
        elif [[ -n "$soak_until" ]]; then
            log "the job supervisor of ${to:0:12} lost the queue within ${HANDOVER_SOAK}s"
            return 1
        elif (( $(now) >= deadline )); then
            log "the job supervisor of ${to:0:12} did not take the queue within ${HANDOVER_CONFIRM}s"
            return 1
        fi
        sleep "$POLL"
    done
}

handover() {  # handover FROM TO BASELINE: 0 done, 1 TO cannot hold the queue, 2 FROM would not let go
    local from="$1" to="$2" baseline="$3"
    $jobs_enabled || return 0
    if is_running "$from"; then
        if signal_if "$from" SIGUSR1 drainable; then
            log "asked the job supervisor in ${from:0:12} to finish its current job and hand over the queue"
        fi
        if ! wait_released "$from"; then
            log "the job supervisor in ${from:0:12} still runs a job after ${HANDOVER_MAX}s"
            return 2
        fi
    fi
    # A drained supervisor retakes the lock only once resumed.
    signal_if "$to" SIGUSR2 passive || true
    confirm_active "$to" "$baseline" || return 1
}

give_back() {  # give_back FROM TO: after a failed handover, TO's supervisor resumes the queue
    $jobs_enabled || return 0
    if is_running "$1" && signal_if "$1" SIGUSR1 drainable; then
        wait_released "$1" || log "WARNING: ${1:0:12} still runs a job; stopping it requeues that job once"
    fi
    if is_running "$2" && signal_if "$2" SIGUSR2 passive; then
        log "resumed the job supervisor in ${2:0:12}"
    fi
}

stop_when_idle() {  # stop_when_idle FROM TO: FROM's supervisor predates handover and cannot drain
    local from="$1" to="$2" deadline idle_until view running queued
    $jobs_enabled && is_running "$from" || return 0
    deadline=$(( $(now) + HANDOVER_MAX ))
    idle_until=$(( $(now) + HANDOVER_IDLE_WAIT ))
    while (( $(now) < deadline )); do
        # It claims queued jobs until it stops. With nothing queued or running
        # it has nothing to claim; after HANDOVER_IDLE_WAIT "nothing running"
        # will do. A job claimed in the instant before SIGTERM is retried once.
        if view="$(worker_view "$to")"; then
            read -r _ _ _ _ running queued <<<"$view"
            if [[ "$running" == 0 && ( "$queued" == 0 || $(now) -ge $idle_until ) ]]; then
                break
            fi
        fi
        sleep "$POLL"
    done
    docker stop --time 45 "$from" >/dev/null 2>&1 || true
    log "stopped ${from:0:12}, whose job supervisor predates handover (${running:-?} running, ${queued:-?} queued)"
}

# ── the interim container ─────────────────────────────────────────────────────

discard_interim() {  # remove it at once: it never served, or no longer serves
    local interim
    interim="$(container_of "$INTERIM_PROJECT")"
    [[ -n "$interim" ]] || return 0
    log "removing the interim container ${interim:0:12}"
    interim_compose down --timeout 10 >/dev/null 2>&1 || docker rm -f "$interim" >/dev/null 2>&1 || true
}

retire_interim() {  # retire_interim SUCCESSOR [RETIRED_NGINX_PID...]: 0 removed, 4 kept (still routed)
    local interim successor="$1"
    shift
    interim="$(container_of "$INTERIM_PROJECT")"
    [[ -n "$interim" ]] || return 0
    detect_jobs "$interim" "$successor"
    give_back "$interim" "$successor"
    drain_http "$interim" "$@" || return $?
    log "removing the interim container ${interim:0:12}"
    interim_compose down --timeout 45 >/dev/null 2>&1 || docker rm -f "$interim" >/dev/null 2>&1 || true
}

record_replaced() {  # record_replaced IMAGE SHA of the release about to be destroyed
    [[ -n "$1" ]] || return 0
    if printf '%s %s\n' "$1" "${2:-unknown}" > "${PREVIOUS_FILE}.new" 2>/dev/null \
        && mv -f "${PREVIOUS_FILE}.new" "$PREVIOUS_FILE" 2>/dev/null; then
        log "recorded ${2:0:12} (${1}) as the release to roll back to"
        return 0
    fi
    rm -f "${PREVIOUS_FILE}.new" 2>/dev/null || true
    log "cannot record the release being replaced in ${PREVIOUS_FILE}; keeping it instead of destroying it"
    return 1
}

# ── undoing ──────────────────────────────────────────────────────────────────

undo_switch() {  # undo_switch CANONICAL INTERIM: traffic and queue back to CANONICAL; 2 or 4
    local canonical="$1" interim="$2" status=0
    if ! switch_to "$CANONICAL_PORT"; then
        log "CRITICAL: could not point nginx back at the previous release"
        return 4
    fi
    local -a retired=("${retired_workers[@]}")
    give_back "$interim" "$canonical"
    drain_http "$interim" "${retired[@]}" || status=$?
    (( status == 0 )) || return "$status"
    discard_interim
    log "the attempt was undone; the previous release serves; retry later"
    return 2
}

recover_to_old() {  # recover_to_old CANONICAL INTERIM OLD_SHA: the new supervisor died after the switch
    local canonical="$1" interim="$2" old_sha="$3" status=0
    log "the new release's job supervisor failed after the switch; returning traffic to ${canonical:0:12}"
    if ! serves "$CANONICAL_PORT" "$old_sha" || ! switch_to "$CANONICAL_PORT"; then
        log "CRITICAL: the previous release cannot take traffic back; the new one keeps it"
        return 4
    fi
    local -a retired=("${retired_workers[@]}")
    drain_http "$interim" "${retired[@]}" || status=$?
    (( status == 0 )) || return "$status"
    discard_interim        # first, so its supervisor cannot take the lock again
    if signal_if "$canonical" SIGUSR2 passive; then log "resumed the job supervisor in ${canonical:0:12}"; fi
    log "REJECTED: the new release's job supervisor could not hold the queue; the previous release serves"
    return 1
}

recover_legacy() {  # recover_legacy CANONICAL INTERIM OLD_SHA: the same after the cut-over deploy
    local canonical="$1" interim="$2" old_sha="$3"
    log "the new release's job supervisor failed; restarting the previous release, which was stopped for it"
    # The candidate goes first so its supervisor cannot keep taking the lock
    # from the older supervisor, which gives up after 30 s. Its web server
    # already fails with its supervisor, so this adds no outage.
    interim_compose stop --timeout 10 >/dev/null 2>&1 || true
    docker start "$canonical" >/dev/null 2>&1 || true
    if ! wait_ready "$canonical" "$CANONICAL_PORT" "$old_sha" || ! switch_to "$CANONICAL_PORT"; then
        log "CRITICAL: the previous release did not come back; bring one up by hand (deploy/README.md, Rollback)"
        return 4
    fi
    discard_interim
    log "REJECTED: the new release's job supervisor could not hold the queue; the previous release serves"
    return 1
}

# ── phases ───────────────────────────────────────────────────────────────────

move_to_canonical() {  # move_to_canonical IMAGE SHA INTERIM: phase 2; 0, 3 or 4
    local image="$1" sha="$2" interim="$3" canonical="" attempt baseline interim_image interim_sha status=0
    local -a recreate=()
    interim_image="$(image_of "$interim")"
    interim_sha="$(sha_of "$interim")"
    for attempt in 1 2; do
        log "starting the canonical container on ${image} for ${sha:0:12} (attempt ${attempt})"
        if PRIVATOOLS_IMAGE="$image" GIT_SHA="$sha" canonical_compose up -d --no-build --pull never "${recreate[@]}" "$SERVICE"; then
            canonical="$(container_of "$COMPOSE_PROJECT")"
            if wait_ready "$canonical" "$CANONICAL_PORT" "$sha" && page_probe "$canonical" "$CANONICAL_PORT" "$sha"; then
                break
            fi
            show_logs "$canonical"
        fi
        canonical=""
        recreate=(--force-recreate)
    done
    if [[ -z "$canonical" ]]; then
        canonical_compose stop --timeout 10 "$SERVICE" >/dev/null 2>&1 || true
        mark_resume
        log "DEGRADED: the canonical container did not come up; ${interim_sha:0:12} keeps serving from the interim container"
        return 3
    fi

    baseline="$(restarts_of "$canonical")"
    detect_jobs "$canonical" "$interim"
    handover "$interim" "$canonical" "$baseline" || status=$?
    if (( status != 0 )); then
        canonical_compose stop --timeout 10 "$SERVICE" >/dev/null 2>&1 || true
        give_back "$canonical" "$interim"
        mark_resume
        log "DEGRADED: the canonical container's job supervisor could not take the queue; the interim keeps serving"
        return 3
    fi
    if ! switch_to "$CANONICAL_PORT" || ! public_serves "$sha"; then
        if ! switch_to "$INTERIM_PORT"; then
            log "CRITICAL: nginx points at neither container in a verified way"
            return 4
        fi
        give_back "$canonical" "$interim"
        canonical_compose stop --timeout 10 "$SERVICE" >/dev/null 2>&1 || true
        mark_resume
        log "DEGRADED: nginx could not be moved back to the canonical container; the interim keeps serving"
        return 3
    fi
    log "traffic is back on the canonical container"
    local -a retired=("${retired_workers[@]}")
    drain_http "$interim" "${retired[@]}" || return $?
    if [[ "$interim_image" != "$(image_id "$image")" ]]; then
        # A rollback from the degraded state replaces the interim's release.
        record_replaced "$interim_image" "$interim_sha" || log "WARNING: the rollback record is stale"
    fi
    log "removing the interim container ${interim:0:12}"
    interim_compose down --timeout 45 >/dev/null 2>&1 || docker rm -f "$interim" >/dev/null 2>&1 || true
    rm -f "$RESUME_FILE"
}

resume_from_interim() {  # resume_from_interim IMAGE SHA ROLLBACK: nginx points at the interim
    local image="$1" sha="$2" rollback="$3" interim interim_image interim_sha canonical c_image c_sha baseline status=0
    interim="$(container_of "$INTERIM_PROJECT")"
    interim_image="$(image_of "$interim")"
    interim_sha="$(sha_of "$interim")"
    if ! $rollback && [[ -f "$RESUME_FILE" ]] \
        && (( $(now) - $(stat -c %Y "$RESUME_FILE" 2>/dev/null || echo 0) < RESUME_BACKOFF )); then
        log "degraded: ${interim_sha:0:12} serves from the interim container; the canonical container failed less than ${RESUME_BACKOFF}s ago"
        return 3
    fi
    if ! $rollback; then
        image="$interim_image"
        sha="$interim_sha"
    fi
    log "resuming: ${interim_sha:0:12} serves from the interim container; moving ${sha:0:12} into the canonical one"
    canonical="$(container_of "$COMPOSE_PROJECT")"
    if is_running "$canonical"; then
        # A run that died after its switch left the replaced container up,
        # possibly mid-request or mid-job: retire it as carefully as phase 2 would.
        c_image="$(image_of "$canonical")"
        c_sha="$(sha_of "$canonical")"
        detect_jobs "$interim" "$canonical"
        baseline="$(restarts_of "$interim")"
        handover "$canonical" "$interim" "$baseline" || status=$?
        if (( status != 0 )); then
            give_back "$interim" "$canonical"
            mark_resume
            log "degraded: the queue could not be handed to the interim container yet"
            return 3
        fi
        drain_http "$canonical" "${retired_workers[@]}" || return $?
        if [[ "$c_image" != "$interim_image" ]] && ! record_replaced "$c_image" "$c_sha"; then
            mark_resume
            return 3
        fi
    elif ! enough_memory; then
        # Nothing is running in the canonical slot, so moving back starts a
        # second container beside the interim.
        if $rollback; then
            return 2
        fi
        mark_resume
        return 3
    fi
    move_to_canonical "$image" "$sha" "$interim"
}

enough_memory() {  # memory for one more container beside those running
    local available
    available="$(awk '/^MemAvailable:/ { print int($2 / 1024) }' "$MEMINFO" 2>/dev/null || true)"
    if [[ -z "$available" ]] || (( available < MIN_AVAILABLE_MB )); then
        log "refusing to start a second container: ${available:-unknown} MB available, ${MIN_AVAILABLE_MB} MB required"
        return 1
    fi
    log "${available} MB available for the overlap"
}

enough_capacity() {
    enough_memory || return 1
    if (exec 3<>"/dev/tcp/127.0.0.1/${INTERIM_PORT}") 2>/dev/null; then
        log "refusing: something already listens on 127.0.0.1:${INTERIM_PORT}"
        return 1
    fi
}

deploy_release() {  # deploy_release IMAGE SHA: phase 1, then phase 2
    local image="$1" sha="$2" container old_image="" old_sha="" canonical="" interim baseline legacy=false status=0
    # The container being replaced is recorded even if it is not running; only
    # a running one is drained and has a job queue to hand over.
    container="$(container_of "$COMPOSE_PROJECT")"
    if [[ -n "$container" ]]; then
        old_image="$(image_of "$container")"
        old_sha="$(sha_of "$container")"
        if [[ "$old_sha" == "$sha" && -n "$old_image" && "$old_image" == "$(image_id "$image")" ]] \
            && serves "$CANONICAL_PORT" "$sha"; then
            log "${sha:0:12} already serves from the canonical container on that image"
            return 0
        fi
        if is_running "$container"; then
            canonical="$container"
        else
            log "the canonical container ${container:0:12} is not running; nothing to drain"
        fi
    fi
    enough_capacity || return 2

    log "phase 1: starting ${sha:0:12} in the interim container on 127.0.0.1:${INTERIM_PORT}"
    if ! PRIVATOOLS_IMAGE="$image" GIT_SHA="$sha" interim_compose up -d --no-build --pull never "$SERVICE"; then
        log "the interim container could not be started (a host or Docker problem); retry later"
        discard_interim
        return 2
    fi
    interim="$(container_of "$INTERIM_PROJECT")"
    if ! wait_ready "$interim" "$INTERIM_PORT" "$sha"; then
        show_logs "$interim"
        log "REJECTED: ${sha:0:12} never became ready; the previous release keeps serving"
        discard_interim
        return 1
    fi
    if ! page_probe "$interim" "$INTERIM_PORT" "$sha"; then
        show_logs "$interim"
        log "REJECTED: ${sha:0:12} is ready but failed the real-page probe; the previous release keeps serving"
        discard_interim
        return 1
    fi

    baseline="$(restarts_of "$interim")"
    detect_jobs "$interim"
    if $jobs_enabled && [[ -n "$canonical" ]] && ! worker_view "$canonical" >/dev/null; then
        legacy=true
        log "the job supervisor in ${canonical:0:12} predates handover: it stops, once idle, after the switch"
    elif $jobs_enabled; then
        handover "$canonical" "$interim" "$baseline" || status=$?
        if (( status != 0 )); then
            show_logs "$interim"
            discard_interim           # first, so a broken supervisor cannot take the lock again
            if [[ -n "$canonical" ]] && signal_if "$canonical" SIGUSR2 passive; then
                log "resumed the job supervisor in ${canonical:0:12}"
            fi
            if (( status == 1 )); then
                log "REJECTED: ${sha:0:12}'s job supervisor could not hold the queue; the previous release keeps serving"
                return 1
            fi
            log "the queue was not handed over; the previous release keeps serving; retry later"
            return 2
        fi
    fi

    if ! switch_to "$INTERIM_PORT" || ! public_serves "$sha"; then
        undo_switch "$canonical" "$interim"
        return $?
    fi
    log "phase 1 done: ${sha:0:12} serves from the interim container"
    if [[ -n "$canonical" ]]; then
        drain_http "$canonical" "${retired_workers[@]}" || return $?
    fi
    if $legacy; then
        stop_when_idle "$canonical" "$interim"
    fi
    # Before anything is destroyed: the new supervisor still holds the queue
    # and its container never restarted.
    if $jobs_enabled && ! confirm_active "$interim" "$baseline"; then
        show_logs "$interim"
        if $legacy; then
            recover_legacy "$canonical" "$interim" "$old_sha"
            return $?
        fi
        if [[ -n "$canonical" ]]; then
            recover_to_old "$canonical" "$interim" "$old_sha"
            return $?
        fi
        log "CRITICAL: the new release's job supervisor failed and there is no previous release to return to"
        return 4
    fi
    if [[ -n "$container" ]] && ! record_replaced "$old_image" "$old_sha"; then
        mark_resume
        log "degraded: ${sha:0:12} serves from the interim container"
        return 3
    fi

    log "phase 2: moving ${sha:0:12} to the canonical container"
    move_to_canonical "$image" "$sha" "$interim" || return $?
    log "done: ${sha:0:12} serves from the canonical container"
}

main() {
    local image sha live rollback=false status=0
    if [[ "$(id -u)" == 0 ]]; then
        log "refusing to run as root: run as the deploy user, e.g. sudo runuser -u ubuntu -g ubuntu -G docker -- privatools-rollout ..."
        exit 2
    fi
    case "${1:-}" in
        --rollback)
            if [[ ! -s "$PREVIOUS_FILE" ]]; then
                log "no previous release recorded in ${PREVIOUS_FILE}"
                exit 2
            fi
            read -r image sha < "$PREVIOUS_FILE"
            rollback=true
            log "rolling back to ${image} (${sha:0:12})"
            ;;
        ""|-*)
            log "usage: $0 IMAGE BUILD_SHA | --rollback"
            exit 2
            ;;
        *)
            image="$1"
            sha="${2:-}"
            [[ -n "$sha" ]] || { log "usage: $0 IMAGE BUILD_SHA | --rollback"; exit 2; }
            ;;
    esac

    if [[ "${PRIVATOOLS_DEPLOY_LOCK_HELD:-}" != 1 ]]; then
        exec 9>>"$LOCK_FILE"
        if ! flock -n 9; then
            log "another deploy is running"
            exit 2
        fi
    fi

    live="$(live_port)"
    if [[ -z "$live" ]]; then
        log "no PrivaTools upstream in ${UPSTREAM_FILE}: install the nginx switch first (deploy/README.md)"
        exit 2
    fi
    if ! grep -q 'proxy_pass http://privatools_app;' "$NGINX_SITE" 2>/dev/null \
        || grep -q 'proxy_pass http://127\.0\.0\.1:' "$NGINX_SITE" 2>/dev/null; then
        log "${NGINX_SITE} does not proxy only through the privatools_app upstream yet (deploy/README.md)"
        exit 2
    fi
    if [[ ! -f "$INTERIM_FILE_PATH" ]] || ! grep -q 'PRIVATOOLS_HOST_PORT' "$COMPOSE_FILE_PATH"; then
        log "the checkout in ${REPO_DIR} predates zero-downtime deploys"
        exit 2
    fi
    if [[ "$live" != "$CANONICAL_PORT" && "$live" != "$INTERIM_PORT" ]]; then
        log "the upstream names port ${live}, neither ${CANONICAL_PORT} nor ${INTERIM_PORT}"
        exit 2
    fi
    cd "$REPO_DIR"

    # The interim mounts exactly what the live container mounts.
    local reference
    reference="$(container_of "$COMPOSE_PROJECT")"
    [[ -n "$reference" ]] || reference="$(container_of "$INTERIM_PROJECT")"
    if [[ -n "$reference" ]]; then
        data_volume="$(mount_of "$reference" /app/data)"
        temp_volume="$(mount_of "$reference" /app/temp)"
    fi
    data_volume="${data_volume:-${COMPOSE_PROJECT}_app-data}"
    temp_volume="${temp_volume:-${COMPOSE_PROJECT}_app-temp}"

    reconcile_nginx "$live" || exit $?
    live="$(live_port)"
    if [[ "$live" == "$INTERIM_PORT" ]]; then
        resume_from_interim "$image" "$sha" "$rollback" || exit $?
    elif [[ -n "$(container_of "$INTERIM_PROJECT")" ]]; then
        log "a previous run left an interim container behind; retiring it"
        retire_interim "$(container_of "$COMPOSE_PROJECT")" "${retired_workers[@]}" || exit $?
    fi
    deploy_release "$image" "$sha" || status=$?
    exit "$status"
}

main "$@"
