from .auth import auth_bp
from .gebruikers import gebruikers_bp
from .main import main_bp
from .evenementen import evenementen_bp
from .kontrakten import kontrakten_bp
from .sponsors import sponsors_bp
from .bestuursleden import bestuursleden_bp
from .sponsoringen import sponsoringen_bp

def register_blueprints(app):
    """Register all blueprints with the app"""
    # Auth blueprint (no prefix)
    app.register_blueprint(auth_bp)
    
    # Main blueprint (no prefix)
    app.register_blueprint(main_bp)
    
    # Feature blueprints with prefixes
    app.register_blueprint(gebruikers_bp, url_prefix='/gebruikers')
    app.register_blueprint(evenementen_bp, url_prefix='/evenementen')
    app.register_blueprint(kontrakten_bp, url_prefix='/kontrakten')
    app.register_blueprint(sponsors_bp, url_prefix='/sponsors')
    app.register_blueprint(bestuursleden_bp, url_prefix='/bestuursleden')
    app.register_blueprint(sponsoringen_bp, url_prefix='/sponsoringen')
