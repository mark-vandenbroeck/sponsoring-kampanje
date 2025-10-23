#!/bin/bash

set -e

ENV=$1
CONTAINER_NAME="sponsoring-app"
IMAGE_NAME="sponsoring-kampanje"

if [ -z "$ENV" ]; then
    echo "Gebruik: $0 [development|production]"
    exit 1
fi

echo "--- HTTPS Deployment voor Sponsoring De Kampanje ---"

echo "--- Docker Compose stoppen en verwijderen (indien actief) ---"
docker-compose down --remove-orphans || true
docker rm -f $CONTAINER_NAME || true

echo "--- SSL Certificaten controleren ---"
if [ ! -f "ssl/sponsoring.crt" ] || [ ! -f "ssl/sponsoring.key" ]; then
    echo "SSL certificaten niet gevonden. Aanmaken van self-signed certificaten..."
    mkdir -p ssl
    
    # Self-signed certificaat voor development
    openssl req -x509 -newkey rsa:4096 -keyout ssl/sponsoring.key -out ssl/sponsoring.crt -days 365 -nodes \
        -subj "/C=BE/ST=Flanders/L=Antwerp/O=Sponsoring De Kampanje/OU=IT/CN=localhost"
    
    echo "✅ Self-signed SSL certificaten aangemaakt"
    echo "⚠️  Voor productie: gebruik Let's Encrypt of commerciële certificaten"
else
    echo "✅ SSL certificaten gevonden"
fi

echo "--- Docker image bouwen: $IMAGE_NAME ---"
docker build -t $IMAGE_NAME .

echo "--- Data en uploads directories voorbereiden ---"
mkdir -p data
mkdir -p data/uploads

# Kopieer bestaande database en uploads als ze lokaal bestaan
if [ -f instance/sponsoring.db ]; then
    echo "Kopiëren van bestaande database naar data/sponsoring.db"
    cp instance/sponsoring.db data/
fi

if [ -d static/uploads ]; then
    echo "Kopiëren van bestaande uploads naar data/uploads"
    cp -r static/uploads/* data/uploads/ || true
fi

if [ "$ENV" == "development" ]; then
    echo "--- Starten in DEVELOPMENT modus met HTTPS ---"
    FLASK_ENV=development docker-compose up -d --build
    echo ""
    echo "🌐 Applicatie beschikbaar op:"
    echo "   - HTTP:  http://localhost (wordt doorgestuurd naar HTTPS)"
    echo "   - HTTPS: https://localhost:5443"
    echo "   - Direct Flask: http://localhost:5100"
    echo ""
    echo "⚠️  Browser waarschuwing verwacht voor self-signed certificaat"
    echo "   Klik 'Advanced' en 'Proceed to localhost (unsafe)'"
    
elif [ "$ENV" == "production" ]; then
    echo "--- Starten in PRODUCTION modus met HTTPS ---"
    # Zorg ervoor dat SECRET_KEY is ingesteld in je omgeving of in docker-compose.yml
    # export SECRET_KEY="your-production-secret-key"
    FLASK_ENV=production docker-compose up -d --build
    echo ""
    echo "🌐 Applicatie beschikbaar op:"
    echo "   - HTTP:  http://your-domain.com (wordt doorgestuurd naar HTTPS)"
    echo "   - HTTPS: https://your-domain.com:5443"
    echo ""
    echo "🔒 HTTPS is geconfigureerd met:"
    echo "   - SSL/TLS versleuteling"
    echo "   - Security headers (HSTS, XSS protection, etc.)"
    echo "   - Rate limiting"
    echo "   - HTTP/2 ondersteuning"
    echo ""
    echo "📋 Voor productie SSL certificaten:"
    echo "   1. Vervang ssl/sponsoring.crt en ssl/sponsoring.key"
    echo "   2. Of gebruik Let's Encrypt: certbot --nginx"
    echo "   3. Of gebruik cloud provider SSL (AWS, Cloudflare, etc.)"
    
else
    echo "Ongeldige omgeving: $ENV. Gebruik 'development' of 'production'."
    exit 1
fi

echo ""
echo "--- Container status controleren ---"
docker-compose ps

echo ""
echo "--- SSL certificaat informatie ---"
if [ -f "ssl/sponsoring.crt" ]; then
    echo "Certificaat details:"
    openssl x509 -in ssl/sponsoring.crt -text -noout | grep -E "(Subject:|Not Before|Not After|Issuer:)"
fi

echo ""
echo "--- Applicatie testen ---"
sleep 5 # Geef de container even de tijd om op te starten

echo "Testing HTTP (should redirect to HTTPS):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}, Redirect: %{redirect_url}\n" http://localhost || echo "HTTP test failed"

echo "Testing HTTPS:"
curl -s -k -o /dev/null -w "HTTPS Status: %{http_code}\n" https://localhost:5443 || echo "HTTPS test failed (expected for self-signed)"

echo ""
echo "--- Logs bekijken (optioneel) ---"
echo "Gebruik 'docker-compose logs -f' om de logs te volgen."
echo ""
echo "🔧 HTTPS Management Commands:"
echo "   - Status: docker-compose ps"
echo "   - Logs: docker-compose logs -f"
echo "   - Restart: docker-compose restart"
echo "   - Stop: docker-compose down"
echo "   - Update: docker-compose pull && docker-compose up -d"
