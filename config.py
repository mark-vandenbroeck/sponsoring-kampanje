import os
from dotenv import load_dotenv

# Get the base directory (where config.py is located)
basedir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Support both postgres:// and postgresql:// for compatibility with deployment platforms like Supabase
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = db_url or f'sqlite:///{os.path.join(basedir, "data", "sponsoring.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB upload limit
    UPLOAD_FOLDER = 'static/uploads'
    
    # SMTP Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() in ('true', '1', 't', 'y', 'yes')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
