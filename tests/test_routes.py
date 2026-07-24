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

def test_logo_db_storage(auth_client, app):
    """Test that logo uploads are stored in the database and served correctly."""
    from app.models import Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring, db
    from datetime import datetime
    import io
    
    # 1. Create dependencies
    with app.app_context():
        ev = Evenement(evenementcode='EVT_TEST', naam='Test Evenement', datum=datetime.now().date(), locatie='Test Locatie')
        db.session.add(ev)
        db.session.flush()
        
        ko = Kontrakt(evenement_id=ev.id, kontrakt='Premium Test', bedrag=500.0)
        sp = Sponsor(naam='Test Sponsor')
        be = Bestuurslid(initialen='TT', naam='Test Member')
        db.session.add_all([ko, sp, be])
        db.session.commit()
        
        ev_id = ev.id
        ko_id = ko.id
        sp_id = sp.id
        be_id = be.id

    # 2. Perform sponsoring add with files
    file_content = b"fake binary image content"
    data = {
        'evenement_id': ev_id,
        'kontrakt_id': ko_id,
        'sponsor_id': sp_id,
        'aangebracht_door_id': be_id,
        'bedrag_kaarten': '',
        'netto_bedrag_excl_btw': '',
        'facturatiebedrag_incl_btw': '',
        'opmerkingen': 'Test database logo storage',
        'logo_origineel': (io.BytesIO(file_content), 'logo_original.png'),
        'logo_afgewerkt': (io.BytesIO(file_content), 'logo_finished.png')
    }
    
    resp = auth_client.post('/sponsoringen/add', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert resp.status_code == 200
    
    # 3. Verify it is stored in database
    with app.app_context():
        sponsoring = Sponsoring.query.filter_by(opmerkingen='Test database logo storage').first()
        assert sponsoring is not None
        assert sponsoring.logo_origineel == 'logo_original.png'
        assert sponsoring.logo_origineel_data == file_content
        assert sponsoring.logo_origineel_mime == 'image/png'
        assert sponsoring.logo_afgewerkt_file == 'logo_finished.png'
        assert sponsoring.logo_afgewerkt_data == file_content
        assert sponsoring.logo_afgewerkt_mime == 'image/png'
        
    # 4. Fetch the file via /uploads/ route
    resp = auth_client.get('/uploads/logo_original.png')
    assert resp.status_code == 200
    assert resp.data == file_content
    assert resp.content_type == 'image/png'

    # 5. Fetch the finished file via /uploads/ route
    resp = auth_client.get('/uploads/logo_finished.png')
    assert resp.status_code == 200
    assert resp.data == file_content
    assert resp.content_type == 'image/png'

def test_force_password_change(client, app):
    """Test that users logging in with default password are forced to change it."""
    from app.models import Gebruiker, db
    
    # 1. Create a user with default password
    with app.app_context():
        u = Gebruiker(email='defaultpass@example.com', rol='gebruiker')
        u.set_password('DeKampanje!1840')
        db.session.add(u)
        db.session.commit()
        
    # 2. Login with the default password should redirect to set_password
    resp = client.post('/login', data={
        'email': 'defaultpass@example.com',
        'password': 'DeKampanje!1840'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'standaard wachtwoord wijzigen' in resp.data or b'wachtwoord instellen' in resp.data
    
    # 3. Accessing dashboard directly should also redirect to set_password
    resp = client.get('/dashboard', follow_redirects=True)
    assert b'Wachtwoord instellen' in resp.data or b'set-password' in resp.data or b'bevestig_wachtwoord' in resp.data or b'wachtwoord' in resp.data

    # 4. Set a new password
    resp = client.post('/set-password', data={
        'password': 'newsecurepassword123',
        'confirm_password': 'newsecurepassword123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Wachtwoord succesvol' in resp.data
    
    # 5. Dashboard should now be accessible
    resp = client.get('/dashboard')
    assert resp.status_code == 200
    assert b'Dashboard' in resp.data

def test_forgot_password_flow(client, app):
    """Test the forgot password code verification and reset flow."""
    from app.models import Gebruiker, db
    
    # 1. Create a user
    with app.app_context():
        u = Gebruiker(email='resetuser@example.com', rol='gebruiker')
        u.set_password('oldpassword123')
        db.session.add(u)
        db.session.commit()
        
    # 2. Trigger forgot password
    resp = client.post('/forgot-password', data={
        'email': 'resetuser@example.com'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'herstelcode naar verzonden' in resp.data
    
    # 3. Retrieve code from DB
    with app.app_context():
        user = Gebruiker.query.filter_by(email='resetuser@example.com').first()
        code = user.reset_code
        assert code is not None
        assert len(code) == 6
        
    # 4. Try invalid code (should increment attempts)
    resp = client.post(f'/reset-password?email=resetuser@example.com', data={
        'code': '000000',
        'new_password': 'newpassword123',
        'confirm_password': 'newpassword123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Ongeldige herstelcode' in resp.data
    
    with app.app_context():
        user = Gebruiker.query.filter_by(email='resetuser@example.com').first()
        assert user.reset_code_pogingen == 1
        
    # 5. Try valid code with mismatching password
    resp = client.post(f'/reset-password?email=resetuser@example.com', data={
        'code': code,
        'new_password': 'newpassword123',
        'confirm_password': 'mismatchpassword'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'komen niet overeen' in resp.data
    
    # 6. Try valid code with valid password
    resp = client.post(f'/reset-password?email=resetuser@example.com', data={
        'code': code,
        'new_password': 'newpassword123',
        'confirm_password': 'newpassword123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'succesvol hersteld' in resp.data
    
    # 7. Check reset fields cleared and password updated
    with app.app_context():
        user = Gebruiker.query.filter_by(email='resetuser@example.com').first()
        assert user.reset_code is None
        assert user.reset_code_pogingen == 0
        assert user.check_password('newpassword123') is True



