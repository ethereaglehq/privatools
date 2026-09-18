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
# The steady state is one container, privatools-privatools-1 on
# 127.0.0.1:8000, exactly as before; the backup, the manual commands in
# deploy/README.md and the CI image probe all rely on that. A rollout passes
# traffic through a temporary second compose project, privatools-interim, on
# 127.0.0.1:8001:
#
#   1. Start the interim container on the new image beside the live one.
#      Wait for /readyz to report BUILD_SHA and for the real-page probe
#      (scripts/ci/probe-image.py --running) to pass. Otherwise remove it and
#      stop: the live release never stopped serving.
#   2. Ask the live container's job supervisor to finish its current job and
#      hand the queue over, switch host nginx to 8001 (nginx -t, graceful
#      reload), and check through nginx that the new build answers.
#   3. Let the old container finish its in-flight requests, including those
#      nginx's retiring workers still pass to it, and wait for the job handover.
#   4. Recreate the canonical container on the new image (compose stops the
#      drained old one), wait for readiness and the page probe again, switch
#      nginx back to 8000, drain the interim container and remove it.
#
# If step 4 cannot bring the canonical container up, the interim keeps serving
# the new release (exit 3, "degraded") and the next run retries after a
# backoff. The site stays up in every failure path.
#
# Exit status:
#   0  BUILD_SHA serves from the canonical container
#   1  the new release was rejected before or during the switch; the previous
#      release still serves and nothing needs rolling back
#   2  refused before starting anything (a precondition failed); nothing changed
#   3  degraded: the new release serves from the interim container
#   4  nginx could not be pointed at a serving container; act now
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
# Uvicorn respawns workers that die at import, so a broken release never
# exits: readiness needs a deadline, and a crash loop is caught early.
READY_TIMEOUT="${READY_TIMEOUT:-180}"
# nginx passes a request to its upstream only after buffering the whole body,
# so an upload that began before a switch can still reach the old container
# from a retiring nginx worker. Keep the old container until that nginx
# generation has exited, or DRAIN_MAX seconds (nginx's 300 s timeouts), and
# then until no request has been in flight on it for DRAIN_QUIET seconds.
DRAIN_MAX="${DRAIN_MAX:-300}"
DRAIN_EXTRA="${DRAIN_EXTRA:-120}"
DRAIN_QUIET="${DRAIN_QUIET:-3}"
# A running async job may take up to runtime_seconds (300 s) to finish.
HANDOVER_MAX="${HANDOVER_MAX:-360}"
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

# Invoked indirectly by the ERR trap below.
# shellcheck disable=SC2329
on_error() {
    log "unexpected failure at line $2 (exit $1); the next run reconciles from the nginx upstream"
}
trap 'on_error "$?" "$LINENO"' ERR

now() { date +%s; }

keep_owner() {  # a manual run as root must not leave files the service (ubuntu) cannot rewrite
    [[ "${EUID}" -eq 0 ]] && chown --reference="$STATE_DIR" "$1" 2>/dev/null
    return 0
}

mark_resume() {  # the canonical container failed: back off before retrying it
    touch "$RESUME_FILE" && keep_owner "$RESUME_FILE"
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

readyz_sha() {  # readyz_sha URL [CURL_ARGS...] -> build_sha when the body says ready
    local body
    body="$(curl --fail --silent --max-time 5 "$@" 2>/dev/null)" || return 1
    [[ "$body" == *'"status":"ready"'* || "$body" == *'"status": "ready"'* ]] || return 1
    sed -n 's/.*"build_sha": *"\([^"]*\)".*/\1/p' <<<"$body"
}

serves() {  # serves PORT SHA
    [[ -n "$2" && "$(readyz_sha "http://127.0.0.1:$1/readyz")" == "$2" ]]
}

public_serves() {  # public_serves SHA: nginx forwards to a ready release reporting SHA
    local -a resolve=()
    local attempt
    [[ -n "$PUBLIC_RESOLVE" ]] && resolve=(--resolve "$PUBLIC_RESOLVE")
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        if [[ "$(readyz_sha "$PUBLIC_READY_URL" "${resolve[@]}")" == "$1" ]]; then
            return 0
        fi
        sleep "$POLL"
    done
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

nginx_workers() {  # PIDs of the current nginx worker processes
    local master
    master="$(cat "$NGINX_PID_FILE" 2>/dev/null || true)"
    [[ "$master" =~ ^[0-9]+$ ]] || return 0
    ps -o pid=,args= --ppid "$master" 2>/dev/null | awk '$2 == "nginx:" && $3 == "worker" { print $1 }' || true
}

alive_workers() {  # alive_workers PID...: those still nginx workers (a reused PID is not)
    local pid
    for pid in "$@"; do
        [[ "$(ps -o args= -p "$pid" 2>/dev/null || true)" == "nginx: worker process"* ]] && printf '%s\n' "$pid"
    done
    return 0
}

switch_to() {  # switch_to PORT; remembers the nginx generation it retires
    local -a command
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

drain_http() {  # drain_http CONTAINER RETIRED_NGINX_PID...
    local container="$1" start quiet_since="" busy old elapsed
    shift
    start="$(now)"
    while :; do
        elapsed=$(( $(now) - start ))
        busy="$(connections "$container")"
        old="$(alive_workers "$@" | wc -l)"
        if (( busy == 0 )); then
            quiet_since="${quiet_since:-$(now)}"
        else
            quiet_since=""
        fi
        if [[ -n "$quiet_since" ]] && (( $(now) - quiet_since >= DRAIN_QUIET )) \
            && (( old == 0 || elapsed >= DRAIN_MAX )); then
            log "${container:0:12} drained after ${elapsed}s (${old} retired nginx workers still open elsewhere)"
            return 0
        fi
        if (( elapsed >= DRAIN_MAX + DRAIN_EXTRA )); then
            log "WARNING: ${busy} requests still open on ${container:0:12} after ${elapsed}s; retiring it anyway"
            return 0
        fi
        sleep "$POLL"
    done
}

# ── async job handover (see backend/app/api_v1/jobs/worker.py) ────────────────

worker_view() {  # worker_view CONTAINER -> "ENABLED ROLE RUNNING QUEUED"; fails for supervisors that cannot drain
    local json
    [[ -n "$1" ]] || return 1
    json="$(docker exec "$1" python -m backend.app.api_v1.jobs.worker --status 2>/dev/null)" || return 1
    "$PYTHON" -c '
import json, sys
state = json.loads(sys.argv[1])
local = state.get("local") or {}
count = lambda name: -1 if state.get(name) is None else state[name]
print("true" if state.get("enabled") else "false", local.get("role") or "none",
      count("running_jobs"), count("queued_jobs"))
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

handover_begin() {  # handover_begin FROM TO: FROM finishes its job and releases; TO may take over
    $jobs_enabled && [[ -n "$1" ]] || return 0
    if [[ -n "${2:-}" ]] && worker_view "$2" >/dev/null; then
        docker kill --signal SIGUSR2 "$2" >/dev/null 2>&1 || true
    fi
    if worker_view "$1" >/dev/null; then
        docker kill --signal SIGUSR1 "$1" >/dev/null 2>&1 || true
        log "asked the job supervisor in ${1:0:12} to finish its current job and hand over the queue"
    else
        log "the job supervisor in ${1:0:12} predates handover; it is stopped once no job runs"
    fi
}

handover_cancel() {  # handover_cancel CONTAINER: its supervisor may take the queue again at once
    $jobs_enabled && [[ -n "$1" ]] || return 0
    if worker_view "$1" >/dev/null; then
        docker kill --signal SIGUSR2 "$1" >/dev/null 2>&1 || true
    fi
}

handover_wait() {  # handover_wait FROM TO: until FROM holds no job, so stopping it interrupts nothing
    $jobs_enabled && [[ -n "$1" ]] || return 0
    local from="$1" to="${2:-}" deadline idle_until view role running queued drainable=false
    worker_view "$from" >/dev/null && drainable=true
    if ! $drainable && ! worker_view "$to" >/dev/null; then
        log "cannot observe either job supervisor; continuing"
        return 0
    fi
    deadline=$(( $(now) + HANDOVER_MAX ))
    idle_until=$(( $(now) + HANDOVER_IDLE_WAIT ))
    while (( $(now) < deadline )); do
        if $drainable; then
            if view="$(worker_view "$from")"; then
                read -r _ role _ <<<"$view"
                if [[ "$role" != active && "$role" != draining ]]; then
                    log "the job supervisor in ${from:0:12} released the queue"
                    confirm_takeover "$to"
                    return 0
                fi
            elif [[ "$(docker inspect -f '{{.State.Running}}' "$from" 2>/dev/null || true)" != true ]]; then
                log "${from:0:12} is no longer running"
                return 0
            fi
        elif view="$(worker_view "$to")"; then
            # An older supervisor cannot drain and claims queued jobs until it
            # stops. With nothing queued or running it has nothing to claim,
            # so stop it then; queued jobs are durable and wait for the new
            # supervisor. After HANDOVER_IDLE_WAIT a busy queue settles for
            # "nothing running": a job claimed in the instant before SIGTERM
            # is then interrupted and retried once, never lost.
            read -r _ _ running queued <<<"$view"
            if [[ "$running" == 0 ]] && [[ "$queued" == 0 ]] || { [[ "$running" == 0 ]] && (( $(now) >= idle_until )); }; then
                docker stop --time 45 "$from" >/dev/null 2>&1 || true
                log "no async job running (${queued} queued); stopped ${from:0:12}, whose supervisor predates handover"
                return 0
            fi
        fi
        sleep "$POLL"
    done
    log "WARNING: the job supervisor in ${from:0:12} still runs a job after ${HANDOVER_MAX}s; stopping it requeues that job once"
}

confirm_takeover() {
    local to="$1" until view role
    [[ -n "$to" ]] || return 0
    until=$(( $(now) + 15 ))
    while (( $(now) < until )); do
        if view="$(worker_view "$to")"; then
            read -r _ role _ <<<"$view"
            if [[ "$role" == active ]]; then
                log "the job supervisor in ${to:0:12} now serves the queue"
                return 0
            fi
        fi
        sleep "$POLL"
    done
    log "note: ${to:0:12} has not taken the queue yet; a drained supervisor retakes it after one lease if nobody does"
}

# ── the interim container ─────────────────────────────────────────────────────

discard_interim() {  # a candidate that never served: remove it at once
    local interim
    interim="$(container_of "$INTERIM_PROJECT")"
    [[ -n "$interim" ]] || return 0
    log "removing the interim container ${interim:0:12}"
    interim_compose down --timeout 10 >/dev/null 2>&1 || docker rm -f "$interim" >/dev/null 2>&1 || true
}

retire_interim() {  # retire_interim SUCCESSOR [RETIRED_NGINX_PID...]: drain, hand over, remove
    local interim successor="$1"
    shift
    interim="$(container_of "$INTERIM_PROJECT")"
    [[ -n "$interim" ]] || return 0
    detect_jobs "$interim" "$successor"
    handover_begin "$interim" "$successor"
    drain_http "$interim" "$@"
    handover_wait "$interim" "$successor"
    log "removing the interim container ${interim:0:12}"
    interim_compose down --timeout 45 >/dev/null 2>&1 || docker rm -f "$interim" >/dev/null 2>&1 || true
}

# ── phases ───────────────────────────────────────────────────────────────────

move_to_canonical() {  # move_to_canonical IMAGE SHA INTERIM: phase 2
    local image="$1" sha="$2" interim="$3" canonical="" attempt
    local -a recreate=()
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
        log "DEGRADED: the canonical container did not come up; ${sha:0:12} keeps serving from the interim container"
        return 3
    fi

    detect_jobs "$canonical" "$interim"
    handover_begin "$interim" "$canonical"
    if ! switch_to "$CANONICAL_PORT"; then
        handover_cancel "$interim"
        mark_resume
        log "DEGRADED: could not switch nginx back to the canonical container; the interim keeps serving"
        return 3
    fi
    if ! public_serves "$sha"; then
        log "nginx does not reach the canonical container; switching back to the interim"
        if ! switch_to "$INTERIM_PORT"; then
            log "CRITICAL: nginx points at 127.0.0.1:${CANONICAL_PORT} but could not be switched back"
            return 4
        fi
        handover_cancel "$interim"
        mark_resume
        return 3
    fi
    log "traffic is back on the canonical container"
    drain_http "$interim" "${retired_workers[@]}"
    handover_wait "$interim" "$canonical"
    log "removing the interim container ${interim:0:12}"
    interim_compose down --timeout 45 >/dev/null 2>&1 || docker rm -f "$interim" >/dev/null 2>&1 || true
    rm -f "$RESUME_FILE"
}

resume_from_interim() {  # nginx points at the interim: finish what a previous run started
    local interim canonical image sha
    interim="$(container_of "$INTERIM_PROJECT")"
    sha="$( [[ -n "$interim" ]] && sha_of "$interim" || true)"
    if [[ -z "$interim" ]] || ! serves "$INTERIM_PORT" "$sha"; then
        log "nginx points at the interim port, but no ready interim container answers there"
        canonical="$(container_of "$COMPOSE_PROJECT")"
        if [[ -n "$canonical" ]] && serves "$CANONICAL_PORT" "$(sha_of "$canonical")" && switch_to "$CANONICAL_PORT"; then
            log "switched nginx back to the canonical container"
            # Its supervisor may still hold the job queue: hand it over first.
            retire_interim "$canonical" "${retired_workers[@]}"
            return 0
        fi
        log "CRITICAL: no container serves; bring one up by hand (deploy/README.md, Rollback)"
        return 4
    fi
    if [[ -f "$RESUME_FILE" ]] && (( $(now) - $(stat -c %Y "$RESUME_FILE") < RESUME_BACKOFF )); then
        log "degraded: ${sha:0:12} serves from the interim container; the canonical container failed less than ${RESUME_BACKOFF}s ago"
        return 3
    fi
    image="$(image_of "$interim")"
    log "resuming: ${sha:0:12} serves from the interim container; moving it back to the canonical one"
    # A run that died right after its switch left the old canonical container
    # up, possibly mid-request or mid-job: retire it as carefully as phase 1.
    canonical="$(container_of "$COMPOSE_PROJECT")"
    if [[ -n "$canonical" && "$(docker inspect -f '{{.State.Running}}' "$canonical" 2>/dev/null || true)" == true ]]; then
        detect_jobs "$interim" "$canonical"
        handover_begin "$canonical" "$interim"
        drain_http "$canonical"
        handover_wait "$canonical" "$interim"
    fi
    move_to_canonical "$image" "$sha" "$interim"
}

enough_capacity() {
    local available
    available="$(awk '/^MemAvailable:/ { print int($2 / 1024) }' "$MEMINFO" 2>/dev/null || true)"
    if [[ -z "$available" ]] || (( available < MIN_AVAILABLE_MB )); then
        log "refusing to start a second container: ${available:-unknown} MB available, ${MIN_AVAILABLE_MB} MB required"
        return 1
    fi
    if (exec 3<>"/dev/tcp/127.0.0.1/${INTERIM_PORT}") 2>/dev/null; then
        log "refusing: something already listens on 127.0.0.1:${INTERIM_PORT}"
        return 1
    fi
    log "${available} MB available for the overlap"
}

deploy_release() {  # deploy_release IMAGE SHA: phase 1, then phase 2
    local image="$1" sha="$2" container old_image="" old_sha="" canonical="" interim
    # The container being replaced is recorded for rollback even if it is not
    # running; only a running one is drained and has a job queue to hand over.
    container="$(container_of "$COMPOSE_PROJECT")"
    if [[ -n "$container" ]]; then
        old_image="$(image_of "$container")"
        old_sha="$(sha_of "$container")"
        if [[ "$old_sha" == "$sha" && -n "$old_image" && "$old_image" == "$(image_id "$image")" ]] \
            && serves "$CANONICAL_PORT" "$sha"; then
            log "${sha:0:12} already serves from the canonical container on that image"
            return 0
        fi
        if [[ "$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null || true)" == true ]]; then
            canonical="$container"
        else
            log "the canonical container ${container:0:12} is not running; nothing to drain"
        fi
    fi
    enough_capacity || return 2

    log "phase 1: starting ${sha:0:12} in the interim container on 127.0.0.1:${INTERIM_PORT}"
    if ! PRIVATOOLS_IMAGE="$image" GIT_SHA="$sha" interim_compose up -d --no-build --pull never "$SERVICE"; then
        log "REJECTED: the interim container could not be created"
        discard_interim
        return 1
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

    detect_jobs "$interim"
    handover_begin "$canonical" "$interim"
    if ! switch_to "$INTERIM_PORT"; then
        handover_cancel "$canonical"
        retire_interim "$canonical"
        log "REJECTED: nginx could not be switched; the previous release keeps serving"
        return 1
    fi
    if ! public_serves "$sha"; then
        log "nginx does not forward to ${sha:0:12}; switching back"
        if ! switch_to "$CANONICAL_PORT"; then
            log "CRITICAL: nginx points at the interim port and could not be switched back"
            return 4
        fi
        handover_cancel "$canonical"
        retire_interim "$canonical" "${retired_workers[@]}"
        log "REJECTED: the switch was undone; the previous release keeps serving"
        return 1
    fi
    log "phase 1 done: ${sha:0:12} serves from the interim container"

    if [[ -n "$canonical" ]]; then
        drain_http "$canonical" "${retired_workers[@]}"
        handover_wait "$canonical" "$interim"
    fi
    log "phase 2: moving ${sha:0:12} to the canonical container"
    move_to_canonical "$image" "$sha" "$interim" || return $?

    if [[ -n "$old_image" && "$old_image" != "$(image_id "$image")" ]]; then
        printf '%s %s\n' "$old_image" "${old_sha:-unknown}" > "$PREVIOUS_FILE"
        keep_owner "$PREVIOUS_FILE"
    fi
    log "done: ${sha:0:12} serves from the canonical container; previous release recorded in ${PREVIOUS_FILE}"
}

main() {
    local image sha live
    case "${1:-}" in
        --rollback)
            if [[ ! -s "$PREVIOUS_FILE" ]]; then
                log "no previous release recorded in ${PREVIOUS_FILE}"
                exit 2
            fi
            read -r image sha < "$PREVIOUS_FILE"
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

    local status=0
    case "$live" in
        "$INTERIM_PORT")
            resume_from_interim || status=$?
            (( status == 0 )) || exit "$status"
            ;;
        "$CANONICAL_PORT")
            if [[ -n "$(container_of "$INTERIM_PROJECT")" ]]; then
                log "a previous run left an interim container behind; retiring it"
                retire_interim "$(container_of "$COMPOSE_PROJECT")"
            fi
            ;;
        *)
            log "the upstream names port ${live}, neither ${CANONICAL_PORT} nor ${INTERIM_PORT}"
            exit 2
            ;;
    esac
    deploy_release "$image" "$sha" || status=$?
    exit "$status"
}

main "$@"
