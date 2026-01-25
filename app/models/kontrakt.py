from . import db

class Kontrakt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'), nullable=False)
    kontrakt = db.Column(db.String(100), nullable=False)
    bedrag = db.Column(db.Float, nullable=False)
    tegenprestatie = db.Column(db.Text)
    
    # Relationships
    sponsoringen = db.relationship('Sponsoring', backref='kontrakt', lazy=True, cascade='all, delete-orphan')
    
    # Unique constraint on evenement + kontrakt
    __table_args__ = (db.UniqueConstraint('evenement_id', 'kontrakt', name='unique_evenement_kontrakt'),)
