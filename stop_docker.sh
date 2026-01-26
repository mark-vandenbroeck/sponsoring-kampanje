#!/bin/bash

APP_NAME="sponsoring-app"

echo "🛑 Stopping Sponsoring App (Docker)..."

if [ "$(docker ps -aq -f name=$APP_NAME)" ]; then
    docker stop $APP_NAME
    docker rm $APP_NAME
    echo "✅ Container $APP_NAME stopped and removed."
else
    echo "⚠️  Container $APP_NAME not found."
fi
