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
    
    return app
