from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, Gebruiker, Evenement, Sponsoring, Sponsor, Bestuurslid
from app.utils import login_required
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = Gebruiker.query.filter_by(email=email).first()
        
        if user:
            # If no password is set at all (fallback for legacy or reset users)
            if not user.password_hash:
                session['user_id'] = user.id
                session['user_email'] = user.email
                user.laatste_activiteit = datetime.utcnow()
                db.session.commit()
                flash('Welkom! Je moet eerst je wachtwoord instellen.', 'info')
                return redirect(url_for('auth.set_password'))
            
            # Normal password check
            elif password and user.check_password(password):
                session['user_id'] = user.id
                session['user_email'] = user.email
                user.laatste_activiteit = datetime.utcnow()
                db.session.commit()
                
                # Check if they logged in with the default password
                if password == 'DeKampanje!1840':
                    flash('Je moet eerst je standaard wachtwoord wijzigen.', 'info')
                    return redirect(url_for('auth.set_password'))
                
                flash('Succesvol ingelogd!', 'success')
                return redirect(url_for('auth.dashboard'))
            else:
                flash('Ongeldige email of wachtwoord.', 'error')
        else:
            flash('Ongeldige email of wachtwoord.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    flash('Je bent uitgelogd.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    user = Gebruiker.query.get(session['user_id'])
    
    # Check if user needs to set password
    if not user.password_hash or user.check_password('DeKampanje!1840'):
        return redirect(url_for('auth.set_password'))
    
    # Get dashboard statistics
    evenementen_count = Evenement.query.count()
    sponsoringen_count = Sponsoring.query.count()
    sponsors_count = Sponsor.query.count()
    bestuursleden_count = Bestuurslid.query.count()
    
    return render_template('dashboard.html', 
                         evenementen_count=evenementen_count,
                         sponsoringen_count=sponsoringen_count,
                         sponsors_count=sponsors_count,
                         bestuursleden_count=bestuursleden_count)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = Gebruiker.query.get(session['user_id'])
        
        if not user.check_password(current_password):
            flash('Huidig wachtwoord is onjuist.', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('Nieuwe wachtwoorden komen niet overeen.', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('Wachtwoord moet minimaal 6 karakters lang zijn.', 'error')
            return render_template('change_password.html')
        
        user.set_password(new_password)
        db.session.commit()
        flash('Wachtwoord succesvol gewijzigd!', 'success')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('change_password.html')

@auth_bp.route('/set-password', methods=['GET', 'POST'])
@login_required
def set_password():
    user = Gebruiker.query.get(session['user_id'])
    
    if user.password_hash and not user.check_password('DeKampanje!1840'):  # User already has a customized password
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Wachtwoorden komen niet overeen.', 'error')
            return render_template('set_password.html')
        
        if len(password) < 6:
            flash('Wachtwoord moet minimaal 6 karakters lang zijn.', 'error')
            return render_template('set_password.html')
        
        user.set_password(password)
        db.session.commit()
        flash('Wachtwoord succesvol ingesteld!', 'success')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('set_password.html')

@auth_bp.route('/backup-database', methods=['POST'])
@login_required
def backup_database():
    from flask import Response
    from sqlalchemy import select
    import io
    import json
    from datetime import datetime, date
    from app.models import db, Gebruiker

    user = Gebruiker.query.get(session['user_id'])
    if user.rol != 'beheerder':
        flash('Geen toegang.', 'error')
        return redirect(url_for('auth.dashboard'))

    try:
        # Volgorde van tabellen om foreign key constraints te respecteren
        tables_order = ['gebruiker', 'evenement', 'bestuurslid', 'kontrakt', 'sponsor', 'sponsoring', 'audit_logs']
        metadata = db.metadata
        sql_output = io.StringIO()

        sql_output.write("-- Sponsoring Database Backup\n")
        sql_output.write(f"-- Gegenereerd op: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Tijdelijk uitschakelen van constraints voor database-agnostische import
        sql_output.write("PRAGMA foreign_keys = OFF;\n")
        sql_output.write("SET CONSTRAINTS ALL DEFERRED;\n\n")

        with db.engine.connect() as conn:
            for table_name in tables_order:
                if table_name not in metadata.tables:
                    continue
                table = metadata.tables[table_name]
                
                # Filter binaire kolommen uit om OOM en timeouts te voorkomen
                blob_columns = ('logo_origineel_data', 'logo_origineel_thumb_data', 'logo_afgewerkt_data', 'logo_afgewerkt_thumb_data')
                columns_to_select = [c for c in table.columns if c.name not in blob_columns]
                
                # Haal alle rijen op met alleen de geselecteerde kolommen
                result = conn.execute(select(*columns_to_select))
                rows = result.fetchall()
                if not rows:
                    continue

                sql_output.write(f"-- Data voor tabel {table_name}\n")
                columns_str = ", ".join([f'"{c.name}"' for c in columns_to_select])

                for row in rows:
                    values = []
                    for col in columns_to_select:
                        val = row._mapping.get(col.name)
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, bool):
                            values.append("TRUE" if val else "FALSE")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        elif isinstance(val, (datetime, date)):
                            values.append(f"'{val.isoformat()}'")
                        elif isinstance(val, (dict, list)):
                            json_str = json.dumps(val).replace("'", "''")
                            values.append(f"'{json_str}'")
                        else:
                            val_str = str(val).replace("'", "''")
                            values.append(f"'{val_str}'")

                    values_str = ", ".join(values)
                    sql_output.write(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});\n")
                sql_output.write("\n")

        sql_output.write("PRAGMA foreign_keys = ON;\n")

        filename = f"sponsoring_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        return Response(
            sql_output.getvalue(),
            mimetype="application/sql",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        flash(f'Fout bij maken backup: {str(e)}', 'error')
        return redirect(url_for('auth.dashboard'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = Gebruiker.query.filter_by(email=email).first()
        
        # Security best practice: don't reveal if the user email exists or not
        flash('Indien het e-mailadres bekend is, is er een herstelcode naar verzonden.', 'info')
        
        if user:
            import random
            # Generate 6-digit code
            code = f"{random.randint(100000, 999999)}"
            user.reset_code = code
            user.reset_code_verloopt = datetime.utcnow() + timedelta(minutes=30)
            user.reset_code_pogingen = 0
            db.session.commit()
            
            # Send email
            try:
                from app.utils.email import send_email
                subject = "Herstelcode voor je wachtwoord - Sponsoring De Kampanje"
                html_content = f"""
                <h3>Beste gebruiker,</h3>
                <p>Er is een verzoek ingediend om het wachtwoord van je account te herstellen.</p>
                <p>Gebruik de volgende 6-digit herstelcode om je wachtwoord opnieuw in te stellen:</p>
                <h2 style="letter-spacing: 5px; font-size: 24px; color: #0d6efd;">{code}</h2>
                <p>De code is <strong>30 minuten</strong> geldig. Je hebt maximaal <strong>5 pogingen</strong>.</p>
                <p>Klik op de onderstaande link of ga naar de herstelpagina in de app om de code in te voeren:</p>
                <p><a href="{request.url_root}reset-password?email={email}">{request.url_root}reset-password?email={email}</a></p>
                <p>Als je dit verzoek niet hebt gedaan, kun je deze e-mail veilig negeren. Je wachtwoord blijft dan ongewijzigd.</p>
                <br>
                <p>Met vriendelijke groet,<br>
                Sponsoring De Kampanje</p>
                """
                send_email(email, subject, html_content)
            except Exception as e:
                # Log error
                from flask import current_app
                current_app.logger.error(f"Fout bij verzenden herstelcode e-mail: {e}")
                
        return redirect(url_for('auth.reset_password', email=email))
        
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def reset_password():
    email = request.args.get('email', '') or request.form.get('email', '')
    email = email.strip()
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        user = Gebruiker.query.filter_by(email=email).first()
        
        if not user:
            flash('Ongeldig e-mailadres.', 'error')
            return redirect(url_for('auth.forgot_password'))
            
        if not user.reset_code:
            flash('Geen actieve herstelcode gevonden voor dit e-mailadres. Vraag een nieuwe code aan.', 'error')
            return redirect(url_for('auth.forgot_password'))
            
        # Check if expired (30 minutes)
        if datetime.utcnow() > user.reset_code_verloopt:
            user.reset_code = None
            user.reset_code_verloopt = None
            user.reset_code_pogingen = 0
            db.session.commit()
            flash('De herstelcode is verlopen (maximaal 30 minuten geldig). Vraag een nieuwe code aan.', 'error')
            return redirect(url_for('auth.forgot_password'))
            
        # Increment attempt counter
        user.reset_code_pogingen += 1
        db.session.commit()
        
        # Check if attempts exceeded (max 5 pogingen)
        if user.reset_code_pogingen > 5:
            user.reset_code = None
            user.reset_code_verloopt = None
            user.reset_code_pogingen = 0
            db.session.commit()
            flash('Te veel mislukte pogingen. De code is ongeldig gemaakt. Vraag een nieuwe code aan.', 'error')
            return redirect(url_for('auth.forgot_password'))
            
        # Check if code matches
        if code != user.reset_code:
            remaining = 5 - user.reset_code_pogingen
            flash(f'Ongeldige herstelcode. Je hebt nog {remaining} poging(en) over.', 'error')
            return render_template('reset_password.html', email=email)
            
        # Validate password length
        if len(new_password) < 6:
            flash('Wachtwoord moet minimaal 6 karakters lang zijn.', 'error')
            return render_template('reset_password.html', email=email)
            
        # Validate password confirmation
        if new_password != confirm_password:
            flash('Wachtwoorden komen niet overeen.', 'error')
            return render_template('reset_password.html', email=email)
            
        # If code matches and validation passes, reset password
        user.set_password(new_password)
        user.reset_code = None
        user.reset_code_verloopt = None
        user.reset_code_pogingen = 0
        db.session.commit()
        
        flash('Je wachtwoord is succesvol hersteld. Je kunt nu inloggen met je nieuwe wachtwoord.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('reset_password.html', email=email)
