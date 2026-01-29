from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models to make them available
from .gebruiker import Gebruiker
from .evenement import Evenement
from .kontrakt import Kontrakt
from .sponsor import Sponsor
from .bestuurslid import Bestuurslid
from .sponsoring import Sponsoring
from .audit_log import AuditLog

__all__ = ['db', 'Gebruiker', 'Evenement', 'Kontrakt', 'Sponsor', 'Bestuurslid', 'Sponsoring', 'AuditLog']
