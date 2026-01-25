from . import db

class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evenementcode = db.Column(db.String(50), nullable=False, unique=True)
    naam = db.Column(db.String(200), nullable=False)
    datum = db.Column(db.Date, nullable=False)
    locatie = db.Column(db.String(200), nullable=False)
    omschrijving = db.Column(db.Text)
    
    # Relationships
    kontrakten = db.relationship('Kontrakt', backref='evenement', lazy=True, cascade='all, delete-orphan')
    sponsoringen = db.relationship('Sponsoring', backref='evenement', lazy=True, cascade='all, delete-orphan')
