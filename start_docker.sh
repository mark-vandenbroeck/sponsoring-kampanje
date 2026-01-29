#!/bin/bash

APP_NAME="sponsoring-app"
IMAGE_NAME="sponsoring-kampanje"
PORT=5100

echo "🐳 Starting Sponsoring App (Docker)..."

# Check if container is already running
if [ "$(docker ps -q -f name=$APP_NAME)" ]; then
    echo "⚠️  Container $APP_NAME is already running."
    echo "📍 URL: http://localhost:$PORT"
    exit 0
fi

# Cleanup stopped/zombie container
if [ "$(docker ps -aq -f name=$APP_NAME)" ]; then
    echo "🧹 Removing old container..."
    docker rm $APP_NAME
fi

# Build image (ensure latest)
echo "🔨 Building image..."
docker build -t $IMAGE_NAME .

# Run container
echo "🚀 Starting container..."
docker run -d -p $PORT:$PORT \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/static/uploads:/app/static/uploads" \
  --name $APP_NAME \
  $IMAGE_NAME

# Check if started
sleep 2
if [ "$(docker ps -q -f name=$APP_NAME)" ]; then
    echo "✅ App started successfully!"
    echo "📍 URL: http://localhost:$PORT"
else
    echo "❌ Failed to start container. Check logs:"
    docker logs $APP_NAME
fi
