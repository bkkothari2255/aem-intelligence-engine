#!/bin/bash

# AEM Intelligence Engine - Backend Manager
# Usage: ./manage-backend.sh [start|stop|restart|status|tail]

BASE_DIR=$(cd "$(dirname "$0")"; pwd)
PID_FILE="$BASE_DIR/intelligence/backend.pid"
LOG_FILE="$BASE_DIR/intelligence/backend.log"
SERVICE_SCRIPT="src/crawler/live_sync_service.py"

function start_service() {
    if [ -f "$PID_FILE" ]; then
        if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ Backend service is already running (PID: $(cat "$PID_FILE"))"
            return
        else
            echo "⚠️  Found stale PID file. Removed."
            rm "$PID_FILE"
        fi
    fi

    echo "🚀 Starting Backend Service..."
    cd intelligence
    source venv/bin/activate
    
    # Run in background with nohup
    # nohup python "$SERVICE_SCRIPT" > backend.log 2>&1 &
    nohup uvicorn src.crawler.live_sync_service:app --host 0.0.0.0 --port 8000 --reload > "$LOG_FILE" 2>&1 &
    
    PID=$!
    echo $PID > "$PID_FILE"
    echo "✅ Service started with PID: $PID"
    echo "📜 Logs: $LOG_FILE"
}

function stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo "🛑 Service is not running (no PID file)."
        return
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        echo "🛑 Stopping service (PID: $PID)..."
        kill $PID
        rm "$PID_FILE"
        echo "✅ Service stopped."
    else
        echo "⚠️  Service process not found. Removing PID file."
        rm "$PID_FILE"
    fi
}

function status_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "✅ Service is RUNNING (PID: $PID)"
        else
            echo "⚠️  Service is NOT RUNNING (Stale PID file found)"
        fi
    else
        echo "⚪ Service is STOPPED"
    fi
}

function tail_logs() {
    echo "📜 Tailing logs (Ctrl+C to exit)..."
    tail -f "$LOG_FILE"
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 1
        start_service
        ;;
    status)
        status_service
        ;;
    tail)
        tail_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|tail}"
        exit 1
        ;;
esac
