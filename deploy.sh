#!/bin/bash

# Sponsoring De Kampanje - Deployment Script
# Usage: ./deploy.sh [production|development]

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="sponsoring-kampanje"

echo "🚀 Deploying Sponsoring De Kampanje ($ENVIRONMENT mode)"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data
mkdir -p static/uploads
mkdir -p backup
mkdir -p config
mkdir -p ssl

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 static/uploads
chmod 755 data

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Build and start services
echo "🔨 Building and starting services..."
if [ "$ENVIRONMENT" = "development" ]; then
    echo "🔧 Development mode - enabling debug..."
    export FLASK_ENV=development
    export FLASK_DEBUG=1
fi

docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Health check
echo "🏥 Performing health check..."
if curl -f http://localhost:5100/ > /dev/null 2>&1; then
    echo "✅ Application is healthy!"
else
    echo "❌ Health check failed!"
    echo "📋 Container logs:"
    docker-compose logs sponsoring-app
    exit 1
fi

# Show status
echo "📊 Deployment status:"
docker-compose ps

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📍 Access URLs:"
echo "   - Local: http://localhost:5100"
echo "   - Network: http://$(hostname -I | awk '{print $1}'):5100"
echo ""
echo "🔑 Default admin login:"
echo "   - Email: admin@kampanje.be"
echo "   - Password: (leave empty on first login)"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop: docker-compose down"
echo "   - Restart: docker-compose restart"
echo "   - Update: ./deploy.sh $ENVIRONMENT"
