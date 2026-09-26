#!/bin/bash
# DEEPHUNT daemon control: ./deephunt.sh start|stop|status [target] [hours]
# The 100-year mode. Runs until you stop it.
DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$DIR/state/daemon.pid"
LOG="$DIR/logs/daemon.out"

case "$1" in
  start)
    TARGETS="${2:-adobe}"; HOURS="${3:-2}"; CYCLES="${4:-1}"; PASSIVE="${5:-}"
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "already running (pid $(cat "$PIDFILE"))"; exit 0
    fi
    rm -f "$DIR/state/STOP"
    cd "$DIR"
    nohup python3 deephunt.py --target "$TARGETS" --daemon \
      --interval-hours "$HOURS" --max-cycles "$CYCLES" $PASSIVE \
      >> "$LOG" 2>&1 &
    echo $! > "$PIDFILE"
    echo "DEEPHUNT daemon started: targets=$TARGETS every ${HOURS}h, ${CYCLES} cycle(s)/run (pid $!) $PASSIVE"
    echo "stop with: ./deephunt.sh stop"
    ;;
  stop)
    touch "$DIR/state/STOP"
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null
      rm -f "$PIDFILE"
    fi
    echo "STOP requested — daemon halts after the current run."
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "running (pid $(cat "$PIDFILE"))"
    else
      echo "not running"
    fi
    ls -t "$DIR"/state/*postmortem*.md 2>/dev/null | head -3
    ;;
  *)
    echo "usage: $0 start|stop|status [targets] [hours] [cycles] [--passive-only]"; exit 1
    ;;
esac
