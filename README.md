# Sponsoring De Kampanje

Een moderne Python Flask applicatie voor het beheren van evenement sponsoringen met volledige authenticatie, rolgebaseerde toegang en export functionaliteit.

## Features

### Core Functionaliteit
- **Evenementen beheer**: Voeg evenementen toe met datum, locatie en omschrijving
- **Sponsor beheer**: Beheer sponsor informatie inclusief adres en contactgegevens
- **Kontrakt beheer**: Definieer verschillende kontrakt types per evenement
- **Sponsoring tracking**: Volg sponsoringen met bedragen, facturatie en betaling status
- **Logo beheer**: Upload en beheer originele en afgewerkte logo's (alle bestandstypen)

### Geavanceerde Features
- **Authenticatie & Autorisatie**: Volledig gebruikerssysteem met rollen (Beheerder, Gebruiker, Lezer)
- **Rolgebaseerde toegang**: Verschillende rechten per gebruikerstype
- **Geavanceerde filtering**: Filter op evenement, kontrakt, sponsor, bestuurslid, status
- **Export functionaliteit**: Excel en PDF export voor alle overzichten
- **Rich text editing**: WYSIWYG editor voor vrije tekstvelden
- **Responsive design**: Werkt perfect op desktop, tablet en mobiel
- **Modern UI**: Strakke interface met levendige maar zachte kleuren
- **File management**: Veilige bestandsuploads met thumbnails en zip downloads

## Installatie

### Vereisten
- Python 3.8 of hoger
- pip (Python package manager)

### Lokale Installatie

1. **Clone de repository:**
```bash
git clone <repository-url>
cd Sponsoring
```

2. **Installeer de vereiste packages:**
```bash
pip install -r requirements.txt
```

3. **Start de applicatie:**
```bash
python app.py
```

4. **Open je browser:**
- Lokale toegang: `http://localhost:5100`
- Netwerk toegang: `http://[jouw-ip]:5100`

### Eerste Setup
Bij de eerste start wordt automatisch:
- Een SQLite database aangemaakt
- Een standaard beheerder account aangemaakt (email: `admin@kampanje.be`)
- De uploads directory aangemaakt

## Deployment

### Productie Deployment

#### Option 1: Docker Deployment (Aanbevolen)

1. **Dockerfile is al aanwezig** in de repository met geoptimaliseerde configuratie:
   - Python 3.11-slim base image
   - Security hardened (non-root user)
   - Health checks geïntegreerd
   - Alle dependencies geïnstalleerd

2. **Eenvoudige deployment:**
```bash
# Build de container
docker build -t sponsoring-kampanje .

# Run met database en uploads persistence
docker run -d -p 5100:5100 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/data/uploads:/app/static/uploads \
  --name sponsoring-app \
  sponsoring-kampanje
```

3. **Met docker-compose (aanbevolen):**
```bash
# Start alle services
docker-compose up -d

# Met Nginx reverse proxy
docker-compose -f docker-compose.yml up -d
```

4. **Met deploy script:**
```bash
# One-command deployment
./deploy.sh production
```

### Docker Setup met Bestaande Data

#### **Volledige Setup (Database + Uploads):**

1. **Voorbereiding:**
```bash
# Maak data directory
mkdir -p data

# Kopieer lokale database
cp instance/sponsoring.db data/

# Kopieer uploads
cp -r static/uploads data/
```

2. **Start container met alle data:**
```bash
docker run -d -p 5100:5100 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/data/uploads:/app/static/uploads \
  --name sponsoring-app \
  sponsoring-kampanje
```

3. **Verificatie:**
```bash
# Check container status
docker ps

# Test applicatie
curl http://localhost:5100

# Bekijk logs
docker logs sponsoring-app
```

#### **Voordelen van Docker Setup:**
- ✅ **Volledige data migratie** - Database + uploads
- ✅ **Persistent storage** - Data blijft behouden
- ✅ **Security hardened** - Non-root user
- ✅ **Health monitoring** - Automatische checks
- ✅ **Production ready** - Geoptimaliseerd voor productie

#### Option 2: Systemd Service (Linux)

1. **Maak service file `/etc/systemd/system/sponsoring.service`:**
```ini
[Unit]
Description=Sponsoring De Kampanje
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Sponsoring
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. **Activeer service:**
```bash
sudo systemctl enable sponsoring.service
sudo systemctl start sponsoring.service
```

#### Option 3: Nginx Reverse Proxy

1. **Nginx configuratie:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /path/to/Sponsoring/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Productie Checklist

- [ ] **Environment variabelen instellen:**
  ```bash
  export FLASK_ENV=production
  export SECRET_KEY=your-secret-key-here
  ```

- [ ] **Database backup:**
  ```bash
  cp instance/sponsoring.db backup/sponsoring-$(date +%Y%m%d).db
  ```

- [ ] **File permissions:**
  ```bash
  chmod 755 static/uploads
  chown -R www-data:www-data static/uploads
  ```

- [ ] **Firewall configuratie:**
  ```bash
  ufw allow 5100
  ```

- [ ] **SSL certificaat** (Let's Encrypt):
  ```bash
  certbot --nginx -d your-domain.com
  ```

### Monitoring & Logging

- **Log files:** Controleer `/var/log/sponsoring/` voor applicatie logs
- **Database backup:** Dagelijkse backup van SQLite database
- **File storage:** Monitor `static/uploads/` disk usage
- **Performance:** Monitor memory en CPU usage

## Database

De applicatie gebruikt SQLite als database. De database wordt automatisch aangemaakt bij de eerste start.

### Database Backup
```bash
# Dagelijkse backup
cp instance/sponsoring.db backup/sponsoring-$(date +%Y%m%d).db

# Restore
cp backup/sponsoring-20240101.db instance/sponsoring.db
```

## Entiteiten

### Gebruiker (Authenticatie)
- Email (uniek)
- Password hash
- Eerste aanmelding (timestamp)
- Laatste activiteit (timestamp)
- Rol (beheerder, gebruiker, lezer)

### Evenement
- Evenementcode (uniek)
- Naam
- Datum
- Locatie
- Omschrijving

### Bestuurslid
- Initialen
- Naam (optioneel)

### Kontrakt
- Evenement (foreign key)
- Kontrakt naam
- Bedrag
- Tegenprestatie (rich text)
- Unieke combinatie evenement + kontrakt

### Sponsor
- Naam
- Adres (straat, huisnummer, postcode, gemeente)
- Kontaktpersoon
- Telefoon
- Email
- BTW-nummer
- Bestuurslid (foreign key)
- Opmerkingen (rich text)

### Sponsoring
- Evenement (foreign key)
- Kontrakt (foreign key)
- Sponsor (foreign key)
- Aangebracht door (foreign key naar bestuurslid)
- Bedrag kaarten
- Netto bedrag excl BTW
- Facturatiebedrag incl BTW
- Gefactureerd (boolean)
- Betaald (boolean)
- Opmerkingen (rich text)
- Logo is bezorgd (boolean)
- Logo is afgewerkt (boolean)
- Logo origineel (file)
- Logo afgewerkt (file)

## Technische Details

### Backend
- **Framework**: Flask met SQLAlchemy ORM
- **Database**: SQLite (productie-ready)
- **Authentication**: Werkzeug security met password hashing
- **File handling**: Secure filename generation met UUID
- **Export**: openpyxl (Excel) en reportlab (PDF)

### Frontend
- **CSS Framework**: Bootstrap 5 met custom CSS
- **Icons**: Font Awesome 6.4.0
- **Rich Text**: Quill.js WYSIWYG editor
- **JavaScript**: Vanilla JS voor interactieve features
- **Responsive**: Mobile-first design

### Security
- **Authentication**: Session-based met werkzeug
- **Authorization**: Role-based access control (RBAC)
- **File uploads**: Secure filename generation
- **Input validation**: Server-side validation
- **CSRF protection**: Flask-WTF (indien geconfigureerd)

## Gebruik

### Eerste Setup
1. **Login als beheerder**: Gebruik `admin@kampanje.be` (geen wachtwoord bij eerste login)
2. **Stel wachtwoord in**: Volg de wizard voor eerste wachtwoord
3. **Maak gebruikers aan**: Ga naar "Gebruikers" om teamleden toe te voegen

### Workflow
1. **Evenementen**: Voeg evenementen toe met datum en details
2. **Kontrakten**: Definieer kontrakt types per evenement
3. **Sponsors**: Registreer sponsor informatie
4. **Bestuursleden**: Voeg bestuursleden toe (voor contacten)
5. **Sponsoringen**: Track alle sponsoringen met bedragen en status
6. **Logo's**: Upload en beheer originele en afgewerkte logo's
7. **Export**: Genereer Excel/PDF rapporten

### Rollen & Rechten
- **Beheerder**: Volledige toegang + gebruikersbeheer + verwijderen
- **Gebruiker**: CRUD operaties op alle data
- **Lezer**: Alleen lezen, geen wijzigingen

### Import Functionaliteit
- **CSV Import**: Scripts beschikbaar voor bulk import van:
  - Evenementen
  - Sponsors  
  - Kontrakten
  - Sponsoringen

## Troubleshooting

### Veelvoorkomende Problemen

#### Port al in gebruik
```bash
# Zoek proces op poort 5100
lsof -ti:5100

# Stop proces
kill -9 <PID>

# Of gebruik andere poort
python app.py --port 5101
```

#### Database problemen
```bash
# Backup maken
cp instance/sponsoring.db backup/

# Database resetten (LET OP: verliest alle data!)
rm instance/sponsoring.db
python app.py
```

#### File upload problemen
```bash
# Controleer permissions
ls -la static/uploads/

# Fix permissions
chmod 755 static/uploads/
chown -R $USER:$USER static/uploads/
```

#### Import errors
```bash
# Reinstalleer packages
pip install --upgrade -r requirements.txt

# Specifieke packages
pip install openpyxl reportlab
```

#### Docker-specifieke problemen

**Container start niet:**
```bash
# Check Docker status
docker ps -a

# Bekijk container logs
docker logs sponsoring-app

# Restart container
docker restart sponsoring-app
```

**Database niet gevonden:**
```bash
# Check volume mounts
docker inspect sponsoring-app

# Kopieer database naar container
docker cp instance/sponsoring.db sponsoring-app:/app/data/

# Restart container
docker restart sponsoring-app
```

**Logo's niet zichtbaar:**
```bash
# Check uploads directory
ls -la data/uploads/

# Kopieer uploads naar container
docker cp static/uploads sponsoring-app:/app/static/

# Restart container
docker restart sponsoring-app
```

**Container performance:**
```bash
# Monitor resource usage
docker stats sponsoring-app

# Check disk usage
docker exec sponsoring-app df -h

# Clean up unused containers
docker system prune
```

### Logs & Debugging

#### Development mode
```bash
export FLASK_DEBUG=1
python app.py
```

#### Production logging
```bash
# Log naar file
python app.py > app.log 2>&1 &

# Met systemd
journalctl -u sponsoring.service -f
```

### Performance Optimalisatie

#### Database optimalisatie
- SQLite is geschikt voor < 100GB data
- Voor grotere datasets: overweeg PostgreSQL
- Regelmatige VACUUM operaties

#### File storage
- Monitor disk usage: `du -sh static/uploads/`
- Implementeer cleanup voor oude bestanden
- Overweeg cloud storage voor productie

## Docker Bestanden

### **Aangemaakte Docker Bestanden:**

#### **Core Docker Files:**
- **`Dockerfile`** - Geoptimaliseerde container configuratie
- **`docker-compose.yml`** - Multi-service orchestration
- **`nginx.conf`** - Reverse proxy configuratie
- **`deploy.sh`** - One-command deployment script
- **`.dockerignore`** - Build optimalisatie

#### **Docker Features:**
- ✅ **Security hardened** - Non-root user, minimal attack surface
- ✅ **Health checks** - Automatische monitoring
- ✅ **Volume persistence** - Database en uploads behouden
- ✅ **Multi-architecture** - ARM64 en AMD64 support
- ✅ **Production ready** - Geoptimaliseerd voor productie

#### **Quick Start Commands:**
```bash
# Build container
docker build -t sponsoring-kampanje .

# Run met data persistence
docker run -d -p 5100:5100 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/data/uploads:/app/static/uploads \
  --name sponsoring-app \
  sponsoring-kampanje

# Met docker-compose
docker-compose up -d

# Met deploy script
./deploy.sh production
```

#### **Container Management:**
```bash
# Status check
docker ps

# View logs
docker logs sponsoring-app

# Stop/start
docker stop sponsoring-app
docker start sponsoring-app

# Remove container
docker rm sponsoring-app
```

## Licentie

Dit project is ontwikkeld voor "Sponsoring De Kampanje".
