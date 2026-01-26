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
    export_routes = [
        ('/sponsoringen/export/excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ('/sponsoringen/export/pdf', 'application/pdf'),
        ('/evenementen/export/excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ('/evenementen/export/pdf', 'application/pdf'),
        ('/kontrakten/export/excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ('/kontrakten/export/pdf', 'application/pdf'),
        ('/sponsors/export/excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ('/sponsors/export/pdf', 'application/pdf'),
        ('/bestuursleden/export/excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ('/bestuursleden/export/pdf', 'application/pdf'),
    ]
    
    for route, expected_type in export_routes:
        resp = auth_client.get(route)
        assert resp.status_code == 200, f"Route {route} returned {resp.status_code}"
        assert resp.content_type == expected_type, f"Route {route} has wrong content type"

def test_rate_limit(client, app):
    """Test rate limiting on login endpoint."""
    # Enable rate limiting for this test
    app.config['RATELIMIT_ENABLED'] = True
    
    # Attempt login 6 times (limit is 5)
    for _ in range(5):
        client.post('/login', data={'email': 'bad@example.com', 'password': 'wrong'})
        
    # The 6th attempt should fail
    resp = client.post('/login', data={'email': 'bad@example.com', 'password': 'wrong'})
    assert resp.status_code == 429
