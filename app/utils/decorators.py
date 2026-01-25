from functools import wraps
from flask import session, redirect, url_for, flash
from app.models import Gebruiker

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def beheerder_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        user = Gebruiker.query.get(session['user_id'])
        if not user or not user.is_beheerder():
            flash('Je hebt geen toegang tot deze functie.', 'error')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def gebruiker_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        user = Gebruiker.query.get(session['user_id'])
        if not user or not user.is_gebruiker():
            flash('Je hebt geen toegang tot deze functie.', 'error')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
