from . import db
from sqlalchemy.orm import deferred

class Sponsoring(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'), nullable=False)
    kontrakt_id = db.Column(db.Integer, db.ForeignKey('kontrakt.id'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    aangebracht_door_id = db.Column(db.Integer, db.ForeignKey('bestuurslid.id'), nullable=False)
    bedrag_kaarten = db.Column(db.Float)
    netto_bedrag_excl_btw = db.Column(db.Float)
    facturatiebedrag_incl_btw = db.Column(db.Float)
    gefactureerd = db.Column(db.Boolean, default=False)
    betaald = db.Column(db.Boolean, default=False)
    opmerkingen = db.Column(db.Text)
    logo_bezorgd = db.Column(db.Boolean, default=False)
    logo_afgewerkt = db.Column(db.Boolean, default=False)
    logo_origineel = db.Column(db.String(255))
    logo_afgewerkt_file = db.Column(db.String(255))
    
    # Binary data columns for database storage (deferred to prevent loading large blobs in standard queries)
    logo_origineel_data = deferred(db.Column(db.LargeBinary, nullable=True))
    logo_origineel_mime = db.Column(db.String(100), nullable=True)
    logo_origineel_thumb_data = deferred(db.Column(db.LargeBinary, nullable=True))
    logo_afgewerkt_data = deferred(db.Column(db.LargeBinary, nullable=True))
    logo_afgewerkt_mime = db.Column(db.String(100), nullable=True)
    logo_afgewerkt_thumb_data = deferred(db.Column(db.LargeBinary, nullable=True))
