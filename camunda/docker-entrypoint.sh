#!/bin/sh

set -e

log() {
    echo "$(date -u '+%Y-%m-%dT%H:%M:%S.000+0000') $1"
}

if [ -z ${WAIT_FOR_HOST+x} ]; then
    log "WAIT_FOR_HOST is not set (using default: postgres)"
    WAIT_FOR_HOST=postgres
fi

if [ -z ${WAIT_FOR_PORT+x} ]; then
    log "WAIT_FOR_PORT is not set (using default: 5432)"
    WAIT_FOR_PORT=5432
fi

if [ -z ${WAIT_FOR_TIMEOUT+x} ]; then
    log "WAIT_FOR_TIMEOUT is not set (using default: 300)"
    WAIT_FOR_TIMEOUT=300
fi

wait_for_port() {
    local HOST=$1
    local PORT=$2
    for i in $(seq 1 $WAIT_FOR_TIMEOUT);
    do
        nc -z $HOST $PORT > /dev/null 2>&1 && log "port $PORT is ready" && return
        log "Waiting $WAIT_FOR_TIMEOUT for $HOST:$PORT to be ready"
        WAIT_FOR_TIMEOUT=$(expr $WAIT_FOR_TIMEOUT - 1)
        sleep 1
    done
    exit 1
}

wait_for_port $WAIT_FOR_HOST $WAIT_FOR_PORT

exec java $JVM_OPTS -jar camunda.jar
