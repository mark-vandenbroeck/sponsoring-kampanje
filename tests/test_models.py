from app.models import Gebruiker, Evenement, Kontrakt, Sponsor, Sponsoring
from datetime import datetime

def test_gebruiker_password_hashing():
    u = Gebruiker(email='test@example.com')
    u.set_password('cat')
    assert u.check_password('cat')
    assert not u.check_password('dog')

def test_evenement_creation(app):
    with app.app_context():
        e = Evenement(
            evenementcode='EVT001',
            naam='Test Event',
            datum=datetime.now().date(),
            locatie='Test Locatie'
        )
        assert e.naam == 'Test Event'

def test_kontrakt_constraints(app):
    from sqlalchemy.exc import IntegrityError
    from app.models import db
    
    with app.app_context():
        e = Evenement(
            evenementcode='EVT001',
            naam='Test Event',
            datum=datetime.now().date(),
            locatie='Test Locatie'
        )
        db.session.add(e)
        db.session.commit()
        
        k1 = Kontrakt(evenement_id=e.id, kontrakt='K1', bedrag=100.0)
        db.session.add(k1)
        db.session.commit()
        
        # Try to add duplicate contract code for same event
        k2 = Kontrakt(evenement_id=e.id, kontrakt='K1', bedrag=200.0)
        db.session.add(k2)
        try:
            db.session.commit()
            assert False, "Should raise IntegrityError"
        except IntegrityError:
            db.session.rollback()

def test_sponsoring_calculations(app):
    from app.utils import get_display_amount
    
    s = Sponsoring(
        netto_bedrag_excl_btw=100.0,
        bedrag_kaarten=50.0
    )
    assert get_display_amount(s) == 150.0
    
    s2 = Sponsoring(netto_bedrag_excl_btw=100.0)
    assert get_display_amount(s2) == 100.0
    
    s3 = Sponsoring(bedrag_kaarten=50.0)
    assert get_display_amount(s3) == 50.0
