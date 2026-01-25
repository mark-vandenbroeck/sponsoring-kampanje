from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, Gebruiker, Evenement, Sponsoring, Sponsor, Bestuurslid
from app.utils import login_required
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = Gebruiker.query.filter_by(email=email).first()
        
        if user:
            # Check if user has no password set (new user)
            if not user.password_hash:
                # Allow login without password for new users (password can be empty or anything)
                session['user_id'] = user.id
                session['user_email'] = user.email
                user.laatste_activiteit = datetime.utcnow()
                db.session.commit()
                flash('Welkom! Je moet eerst je wachtwoord instellen.', 'info')
                return redirect(url_for('auth.set_password'))
            elif password and user.check_password(password):
                # Normal login with password
                session['user_id'] = user.id
                session['user_email'] = user.email
                user.laatste_activiteit = datetime.utcnow()
                db.session.commit()
                flash('Succesvol ingelogd!', 'success')
                return redirect(url_for('auth.dashboard'))
            else:
                flash('Ongeldige email of wachtwoord.', 'error')
        else:
            flash('Ongeldige email of wachtwoord.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    flash('Je bent uitgelogd.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    user = Gebruiker.query.get(session['user_id'])
    
    # Check if user needs to set password
    if not user.password_hash:
        return redirect(url_for('auth.set_password'))
    
    # Get dashboard statistics
    evenementen_count = Evenement.query.count()
    sponsoringen_count = Sponsoring.query.count()
    sponsors_count = Sponsor.query.count()
    bestuursleden_count = Bestuurslid.query.count()
    
    return render_template('dashboard.html', 
                         evenementen_count=evenementen_count,
                         sponsoringen_count=sponsoringen_count,
                         sponsors_count=sponsors_count,
                         bestuursleden_count=bestuursleden_count)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = Gebruiker.query.get(session['user_id'])
        
        if not user.check_password(current_password):
            flash('Huidig wachtwoord is onjuist.', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('Nieuwe wachtwoorden komen niet overeen.', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('Wachtwoord moet minimaal 6 karakters lang zijn.', 'error')
            return render_template('change_password.html')
        
        user.set_password(new_password)
        db.session.commit()
        flash('Wachtwoord succesvol gewijzigd!', 'success')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('change_password.html')

@auth_bp.route('/set-password', methods=['GET', 'POST'])
@login_required
def set_password():
    user = Gebruiker.query.get(session['user_id'])
    
    if user.password_hash:  # User already has a password
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Wachtwoorden komen niet overeen.', 'error')
            return render_template('set_password.html')
        
        if len(password) < 6:
            flash('Wachtwoord moet minimaal 6 karakters lang zijn.', 'error')
            return render_template('set_password.html')
        
        user.set_password(password)
        db.session.commit()
        flash('Wachtwoord succesvol ingesteld!', 'success')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('set_password.html')
