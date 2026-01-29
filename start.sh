#!/bin/bash

# Configuration
PORT=5100
WORKERS=4
PID_FILE="app.pid"

echo "🚀 Starting Sponsoring App..."

# Check if already running
if [ -f $PID_FILE ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        echo "❌ App is already running (PID: $PID)"
        exit 1
    else
        echo "⚠️  Stale PID file found. Removing..."
        rm $PID_FILE
    fi
fi

# Start Gunicorn in background
gunicorn -w $WORKERS -b 0.0.0.0:$PORT run:app --daemon --pid $PID_FILE --access-logfile access.log --error-logfile error.log

# Verify start
sleep 2
if [ -f $PID_FILE ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        echo "✅ App started successfully!"
        echo "📍 URL: http://localhost:$PORT"
        echo "🆔 PID: $PID"
    else
        echo "❌ App failed to start."
        exit 1
    fi
else
    echo "❌ App failed to start (No PID file)."
    exit 1
fi
