from . import db

class Bestuurslid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    initialen = db.Column(db.String(10), nullable=False)
    naam = db.Column(db.String(100), nullable=True)
    
    # Relationships
    sponsors = db.relationship('Sponsor', backref='bestuurslid', lazy=True)
    sponsoringen = db.relationship('Sponsoring', backref='aangebracht_door', lazy=True)
