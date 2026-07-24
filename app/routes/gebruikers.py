from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, Gebruiker
from app.utils import beheerder_required

gebruikers_bp = Blueprint('gebruikers', __name__)

@gebruikers_bp.route('/')
@beheerder_required
def list():
    from flask import request
    
    # Sort parameters
    sort = request.args.get('sort', 'email')
    direction = request.args.get('dir', 'asc')
    
    query = Gebruiker.query
    
    if sort == 'email':
        if direction == 'desc':
            query = query.order_by(Gebruiker.email.desc())
        else:
            query = query.order_by(Gebruiker.email.asc())
    elif sort == 'rol':
        if direction == 'desc':
            query = query.order_by(Gebruiker.rol.desc())
        else:
            query = query.order_by(Gebruiker.rol.asc())
            
    gebruikers = query.all()
    return render_template('gebruikers.html', gebruikers=gebruikers, selected_sort=sort, selected_dir=direction)

@gebruikers_bp.route('/toevoegen', methods=['GET', 'POST'])
@beheerder_required
def add():
    if request.method == 'POST':
        email = request.form['email']
        rol = request.form['rol']
        
        # Check if user already exists
        if Gebruiker.query.filter_by(email=email).first():
            flash('Een gebruiker met dit email adres bestaat al.', 'error')
            return render_template('gebruiker_toevoegen.html')
        
        # Create new user
        gebruiker = Gebruiker(
            email=email,
            rol=rol
        )
        gebruiker.set_password('DeKampanje!1840')
        db.session.add(gebruiker)
        db.session.commit()
        
        flash(f"Gebruiker {email} is toegevoegd met het standaard wachtwoord 'DeKampanje!1840'. Ze moeten dit wachtwoord wijzigen bij de eerste login.", 'success')
        return redirect(url_for('gebruikers.list'))
    
    return render_template('gebruiker_toevoegen.html')

@gebruikers_bp.route('/<int:user_id>/bewerken', methods=['GET', 'POST'])
@beheerder_required
def edit(user_id):
    gebruiker = Gebruiker.query.get_or_404(user_id)
    
    if request.method == 'POST':
        gebruiker.email = request.form['email']
        gebruiker.rol = request.form['rol']
        db.session.commit()
        
        flash('Gebruiker succesvol bijgewerkt.', 'success')
        return redirect(url_for('gebruikers.list'))
    
    return render_template('gebruiker_bewerken.html', gebruiker=gebruiker)

@gebruikers_bp.route('/<int:user_id>/verwijderen', methods=['POST'])
@beheerder_required
def delete(user_id):
    gebruiker = Gebruiker.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if gebruiker.id == session['user_id']:
        flash('Je kunt jezelf niet verwijderen.', 'error')
        return redirect(url_for('gebruikers.list'))
    
    # Prevent deleting the last admin
    if gebruiker.rol == 'beheerder' and Gebruiker.query.filter_by(rol='beheerder').count() <= 1:
        flash('Je kunt de laatste beheerder niet verwijderen.', 'error')
        return redirect(url_for('gebruikers.list'))
    
    db.session.delete(gebruiker)
    db.session.commit()
    
    flash('Gebruiker succesvol verwijderd.', 'success')
    return redirect(url_for('gebruikers.list'))

@gebruikers_bp.route('/<int:user_id>/wachtwoord-reset', methods=['POST'])
@beheerder_required
def reset_password(user_id):
    gebruiker = Gebruiker.query.get_or_404(user_id)
    
    # Reset password by setting it to the default password
    gebruiker.set_password('DeKampanje!1840')
    db.session.commit()
    
    flash(f"Wachtwoord van {gebruiker.email} is gereset naar 'DeKampanje!1840'. De gebruiker moet dit wachtwoord wijzigen bij de volgende login.", 'success')
    return redirect(url_for('gebruikers.list'))
