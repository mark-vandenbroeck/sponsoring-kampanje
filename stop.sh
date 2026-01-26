#!/bin/bash

# Configuration
PID_FILE="app.pid"

echo "🛑 Stopping Sponsoring App..."

if [ -f $PID_FILE ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "✅ App stopped (PID: $PID)"
        rm $PID_FILE
    else
        echo "⚠️  Process not found (PID: $PID). Removing stale PID file."
        rm $PID_FILE
    fi
else
    echo "⚠️  No PID file found."
    # Fallback: Find by name
    PIDS=$(pgrep -f "gunicorn.*run:app")
    if [ -n "$PIDS" ]; then
        echo "Found running processes via name. Killing..."
        echo "$PIDS" | xargs kill
        echo "✅ App stopped."
    else
        echo "No running app found."
    fi
fi
