#!/bin/bash

set -e

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Gebruik: $0 <domain> <email>"
    echo "Voorbeeld: $0 sponsoring.kampanje.be admin@kampanje.be"
    exit 1
fi

echo "--- Let's Encrypt SSL Setup voor $DOMAIN ---"

echo "--- Certbot installeren ---"
# Voor Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
elif command -v yum &> /dev/null; then
    # Voor CentOS/RHEL
    sudo yum install -y certbot python3-certbot-nginx
elif command -v brew &> /dev/null; then
    # Voor macOS
    brew install certbot
else
    echo "❌ Certbot niet gevonden. Installeer handmatig:"
    echo "   Ubuntu/Debian: sudo apt-get install certbot python3-certbot-nginx"
    echo "   CentOS/RHEL: sudo yum install certbot python3-certbot-nginx"
    echo "   macOS: brew install certbot"
    exit 1
fi

echo "--- Nginx configuratie updaten voor $DOMAIN ---"
cat > nginx-letsencrypt.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream sponsoring_app {
        server sponsoring-app:5100;
    }

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name $DOMAIN;

        # Let's Encrypt challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect all other traffic to HTTPS
        location / {
            return 301 https://\$host\$request_uri;
        }
    }

    server {
        listen 443 ssl http2;
        server_name $DOMAIN;

        # SSL configuration (will be updated by certbot)
        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Static files
        location /static {
            alias /app/static;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Main application
        location / {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://sponsoring_app;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header X-Forwarded-Host \$host;
            proxy_set_header X-Forwarded-Port \$server_port;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check
        location /health {
            access_log off;
            proxy_pass http://sponsoring_app;
        }
    }
}
EOF

echo "--- Docker-compose voor Let's Encrypt updaten ---"
cat > docker-compose-letsencrypt.yml << EOF
version: '3.8'

services:
  sponsoring-app:
    build: .
    ports:
      - "5100:5100"
    volumes:
      # Persist database
      - ./data:/app/data
      # Persist uploads
      - ./static/uploads:/app/static/uploads
      # Optional: mount config
      - ./config:/app/config:ro
    environment:
      - FLASK_ENV=production
      - FLASK_APP=app.py
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5100/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-letsencrypt.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/certbot:/var/www/certbot
    depends_on:
      - sponsoring-app
    restart: unless-stopped

  certbot:
    image: certbot/certbot
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt
      - /var/www/certbot:/var/www/certbot
    command: certonly --webroot --webroot-path=/var/www/certbot --email $EMAIL --agree-tos --no-eff-email -d $DOMAIN
EOF

echo "--- SSL certificaat aanvragen ---"
echo "⚠️  Zorg ervoor dat:"
echo "   1. Domein $DOMAIN wijst naar deze server"
echo "   2. Poort 80 en 443 zijn open in firewall"
echo "   3. Geen andere webserver draait op poort 80"

read -p "Druk Enter om door te gaan met SSL certificaat aanvraag..."

# Start containers
echo "--- Containers starten ---"
docker-compose -f docker-compose-letsencrypt.yml up -d

# Wacht tot containers draaien
sleep 10

# Vraag SSL certificaat aan
echo "--- SSL certificaat aanvragen via Let's Encrypt ---"
docker-compose -f docker-compose-letsencrypt.yml run --rm certbot

# Herstart Nginx met nieuwe certificaten
echo "--- Nginx herstarten met SSL certificaten ---"
docker-compose -f docker-compose-letsencrypt.yml restart nginx

echo ""
echo "✅ Let's Encrypt SSL setup voltooid!"
echo ""
echo "🌐 Applicatie beschikbaar op:"
echo "   - HTTP:  http://$DOMAIN (wordt doorgestuurd naar HTTPS)"
echo "   - HTTPS: https://$DOMAIN"
echo ""
echo "🔒 SSL certificaat details:"
echo "   - Domein: $DOMAIN"
echo "   - Verlengt automatisch elke 3 maanden"
echo "   - Vertrouwd door alle browsers"
echo ""
echo "📋 Certificaat vernieuwing:"
echo "   - Automatisch: sudo crontab -e"
echo "   - Handmatig: docker-compose -f docker-compose-letsencrypt.yml run --rm certbot renew"
echo ""
echo "🔧 Management commands:"
echo "   - Status: docker-compose -f docker-compose-letsencrypt.yml ps"
echo "   - Logs: docker-compose -f docker-compose-letsencrypt.yml logs -f"
echo "   - Restart: docker-compose -f docker-compose-letsencrypt.yml restart"
