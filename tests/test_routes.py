def test_index(client):
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Inloggen' in response.data

def test_login_logout(client, app):
    from app.models import Gebruiker, db
    
    # Create user
    with app.app_context():
        u = Gebruiker(email='login@example.com', rol='gebruiker')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()
    
    # Login
    resp = client.post('/login', data={
        'email': 'login@example.com',
        'password': 'pass'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Dashboard' in resp.data
    
    # Logout
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Je bent uitgelogd' in resp.data

def test_protected_routes(client):
    """Test that routes require login."""
    routes = [
        '/evenementen/',
        '/kontrakten/',
        '/sponsors/',
        '/sponsoringen/'
    ]
    for route in routes:
        resp = client.get(route, follow_redirects=True)
        # Should redirect to login
        assert b'Inloggen' in resp.data

def test_evenementen_access(auth_client):
    """Test access to evenementen list for logged in user."""
    resp = auth_client.get('/evenementen/')
    assert resp.status_code == 200
    assert b'Evenementen' in resp.data

def test_export_access(auth_client):
    """Test availability of export routes."""
    # Note: These might return redirects or data depending on DB state, 
    # but initially we check valid status code (200 is fine if it renders or downloads)
    # Actually export routes return a file download or 200
    
    # Verify routes exist and don't 404
    resp = auth_client.get('/sponsoringen/export/excel')
    assert resp.status_code == 200
    assert resp.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
