from . import db

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(200), nullable=False)
    straat = db.Column(db.String(100))
    huisnummer = db.Column(db.String(10))
    postcode = db.Column(db.String(10))
    gemeente = db.Column(db.String(100))
    kontaktpersoon = db.Column(db.String(100))
    telefoon = db.Column(db.String(20))
    email = db.Column(db.String(100))
    btw_nummer = db.Column(db.String(50))
    bestuurslid_id = db.Column(db.Integer, db.ForeignKey('bestuurslid.id'))
    opmerkingen = db.Column(db.Text)
    
    # Relationships
    sponsoringen = db.relationship('Sponsoring', backref='sponsor', lazy=True, cascade='all, delete-orphan')
