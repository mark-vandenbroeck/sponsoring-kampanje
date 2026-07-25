from flask import Flask, session
from flask_wtf.csrf import CSRFProtect
import os

from config import config
from app.models import db, Gebruiker
from app.routes import register_blueprints
from app.utils import format_european_currency, get_display_amount
from app.utils.thumbnails import get_thumbnail_path as _get_thumbnail_path

csrf = CSRFProtect()

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure directories exist
    upload_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'])
    data_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(upload_folder_path, exist_ok=True)
    os.makedirs(data_folder_path, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    
    from app.extensions import limiter
    limiter.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register template globals
    app.jinja_env.globals.update(
        format_european_currency=format_european_currency,
        get_display_amount=get_display_amount
    )
    
    # Wrapper function for get_thumbnail_path that has access to app.config
    def get_thumbnail_path(filename):
        # Use absolute path for upload folder
        upload_folder_abs = os.path.join(os.path.dirname(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'])
        return _get_thumbnail_path(filename, upload_folder_abs)
    
    app.jinja_env.globals.update(get_thumbnail_path=get_thumbnail_path)
    
    # Context processor for current_user
    @app.context_processor
    def inject_user():
        current_user = None
        if 'user_id' in session:
            current_user = Gebruiker.query.get(session['user_id'])
        return dict(current_user=current_user)
    
    # Create tables and seed admin user
    with app.app_context():
        # Handle database table creation gracefully in multi-worker environments
        try:
            db.create_all()
            
            # Ensure password reset columns exist on the gebruiker table (database-agnostic)
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'gebruiker' in inspector.get_table_names():
                columns = [c['name'] for c in inspector.get_columns('gebruiker')]
                if 'reset_code' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE gebruiker ADD COLUMN reset_code VARCHAR(6)"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                if 'reset_code_verloopt' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE gebruiker ADD COLUMN reset_code_verloopt TIMESTAMP"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                if 'reset_code_pogingen' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE gebruiker ADD COLUMN reset_code_pogingen INTEGER DEFAULT 0"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
            
            # Ensure Sponsoring binary upload columns exist on the sponsoring table
            if 'sponsoring' in inspector.get_table_names():
                columns = [c['name'] for c in inspector.get_columns('sponsoring')]
                if 'logo_origineel_data' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE sponsoring ADD COLUMN logo_origineel_data BLOB"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                if 'logo_origineel_mime' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE sponsoring ADD COLUMN logo_origineel_mime VARCHAR(100)"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                if 'logo_origineel_thumb_data' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE sponsoring ADD COLUMN logo_origineel_thumb_data BLOB"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                if 'logo_afgewerkt_data' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE sponsoring ADD COLUMN logo_afgewerkt_data BLOB"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                if 'logo_afgewerkt_mime' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE sponsoring ADD COLUMN logo_afgewerkt_mime VARCHAR(100)"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                if 'logo_afgewerkt_thumb_data' not in columns:
                    try:
                        db.session.execute(text("ALTER TABLE sponsoring ADD COLUMN logo_afgewerkt_thumb_data BLOB"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
            
            # Ensure indexes exist on foreign keys (database-agnostic)
            try:
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_sponsoring_evenement_id ON sponsoring (evenement_id)"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_sponsoring_kontrakt_id ON sponsoring (kontrakt_id)"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_sponsoring_sponsor_id ON sponsoring (sponsor_id)"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_sponsoring_aangebracht_door_id ON sponsoring (aangebracht_door_id)"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_sponsor_bestuurslid_id ON sponsor (bestuurslid_id)"))
                db.session.commit()
            except Exception as idx_err:
                db.session.rollback()
                app.logger.warning(f"Failed to create indexes: {idx_err}")
        except Exception as e:
            app.logger.warning(f"Database table creation check or reset columns check encountered an error: {e}")
        
        # Ensure default admin user exists, handling potential concurrent inserts
        try:
            admin_user = Gebruiker.query.filter_by(email='admin@kampanje.be').first()
            if not admin_user:
                admin_user = Gebruiker(
                    email='admin@kampanje.be',
                    rol='beheerder'
                )
                admin_user.set_password('DeKampanje!1840')
                db.session.add(admin_user)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Admin seeding encountered an error (likely due to concurrent worker startup): {e}")
        
         # Register audit listeners
        from app.audit import register_audit_listeners
        register_audit_listeners(app, db)
        
        # Global error handler to mail administrators on unhandled exceptions (500)
        @app.errorhandler(Exception)
        def handle_exception(e):
            # Pass through HTTP exceptions
            from werkzeug.exceptions import HTTPException
            if isinstance(e, HTTPException):
                return e
                
            import traceback
            from datetime import datetime
            from flask import request, session
            from app.models import Gebruiker
            from app.utils.email import send_email
            
            tb = traceback.format_exc()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Safe session user details extraction
            user_info = "Niet ingelogd"
            if 'user_id' in session:
                try:
                    # Rollback session to clear any failed state before querying
                    db.session.rollback()
                    user = Gebruiker.query.get(session['user_id'])
                    if user:
                        user_info = f"{user.email} (Rol: {user.rol}, ID: {user.id})"
                except Exception:
                    user_info = f"User ID: {session['user_id']} (Kon details niet laden)"
            
            request_url = request.url
            request_method = request.method
            request_args = dict(request.args)
            request_form = {k: v for k, v in request.form.items() if 'password' not in k.lower()}
            
            subject = "⚠️ Kritieke Fout in Sponsoring De Kampanje"
            html_content = f"""
            <h2>Kritieke Foutrapportage</h2>
            <p>Er heeft zich een onverwachte fout voorgedaan in de Sponsoring-applicatie.</p>
            
            <h3>Details:</h3>
            <ul>
                <li><strong>Tijdstip:</strong> {timestamp}</li>
                <li><strong>Gebruiker:</strong> {user_info}</li>
                <li><strong>URL:</strong> {request_url}</li>
                <li><strong>Method:</strong> {request_method}</li>
                <li><strong>URL Parameters:</strong> {request_args}</li>
                <li><strong>Form Data (beveiligd):</strong> {request_form}</li>
                <li><strong>Foutmelding:</strong> {str(e)}</li>
            </ul>
            
            <h3>Traceback:</h3>
            <pre style="background-color: #f8f9fa; padding: 10px; border: 1px solid #e1e8ed; overflow-x: auto; font-family: monospace; font-size: 12px;">{tb}</pre>
            
            <p><em>Dit is een automatisch gegenereerde e-mail van het Sponsoring Management Systeem.</em></p>
            """
            
            # Find all administrator emails
            admin_emails = []
            try:
                db.session.rollback()
                admins = Gebruiker.query.filter_by(rol='beheerder').all()
                admin_emails = [a.email for a in admins if a.email]
            except Exception as db_err:
                app.logger.error(f"Fout bij ophalen beheerders voor foutrapportage: {db_err}")
                
            if not admin_emails:
                admin_emails = ['admin@kampanje.be']
                
            for email in admin_emails:
                try:
                    send_email(email, subject, html_content)
                except Exception as mail_err:
                    app.logger.error(f"Fout bij verzenden foutrapportage naar {email}: {mail_err}")
            
            return """
            <!DOCTYPE html>
            <html lang="nl">
            <head>
                <meta charset="UTF-8">
                <title>Internal Server Error</title>
                <style>
                    body { font-family: sans-serif; text-align: center; padding: 50px; background-color: #FAFBFC; color: #2C3E50; }
                    h1 { color: #E74C3C; }
                    p { color: #7F8C8D; }
                    a { color: #4A90E2; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1>Oeps, er ging iets mis!</h1>
                <p>Er is een interne fout opgetreden in de applicatie. De beheerders zijn hiervan automatisch per e-mail op de hoogte gesteld.</p>
                <a href="/">Terug naar home</a>
            </body>
            </html>
            """, 500
    
    return app
