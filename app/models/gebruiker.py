from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class Gebruiker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for new users
    eerste_aanmelding = db.Column(db.DateTime, default=datetime.utcnow)
    laatste_activiteit = db.Column(db.DateTime, default=datetime.utcnow)
    rol = db.Column(db.String(20), nullable=False, default='lezer')  # beheerder, gebruiker, lezer
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_beheerder(self):
        return self.rol == 'beheerder'
    
    def is_gebruiker(self):
        return self.rol in ['beheerder', 'gebruiker']
    
    def is_lezer(self):
        return self.rol in ['beheerder', 'gebruiker', 'lezer']
