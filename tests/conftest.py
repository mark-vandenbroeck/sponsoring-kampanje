import pytest
import os
import sys

# Ensure app is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Gebruiker, Evenement, Sponsor, Bestuurslid

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    # Create tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client, app):
    """A test client with a logged-in user."""
    # Create a user
    with app.app_context():
        u = Gebruiker(email='test@example.com', rol='beheerder')
        u.set_password('password')
        db.session.add(u)
        db.session.commit()
    
    # Login
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password'
    }, follow_redirects=True)
    
    return client
