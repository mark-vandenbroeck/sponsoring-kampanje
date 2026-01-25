from flask import Blueprint, render_template, redirect, url_for, flash
from app.utils import login_required, gebruiker_required, beheerder_required
from app.models import Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring

kontrakten_bp = Blueprint('kontrakten', __name__)

@kontrakten_bp.route('/')
@login_required
def list():
    from flask import request
    
    # Get filter parameter
    evenement_filter = request.args.get('evenement', '')
    
    # If no evenement filter is provided, default to the most recent event
    if not evenement_filter:
        latest_evenement = Evenement.query.order_by(Evenement.datum.desc()).first()
        if latest_evenement:
            evenement_filter = str(latest_evenement.id)
    
    # Query kontrakten
    if evenement_filter:
        kontrakten = Kontrakt.query.filter_by(evenement_id=int(evenement_filter)).all()
    else:
        kontrakten = Kontrakt.query.all()
    
    # Calculate total bedrag
    total_bedrag = sum(k.bedrag for k in kontrakten if k.bedrag is not None)
    
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    return render_template('kontrakten.html', kontrakten=kontrakten, evenementen=evenementen, 
                         selected_evenement=evenement_filter, selected_sort='evenement', 
                         selected_dir='asc', total_bedrag=total_bedrag)

@kontrakten_bp.route('/add', methods=['GET', 'POST'])
@gebruiker_required
def add():
    from flask import request
    from app.models import db
    
    if request.method == 'POST':
        kontrakt = Kontrakt(
            evenement_id=int(request.form['evenement_id']),
            kontrakt=request.form['kontrakt'],
            bedrag=float(request.form['bedrag']),
            tegenprestatie=request.form.get('tegenprestatie', '')
        )
        db.session.add(kontrakt)
        db.session.commit()
        flash(f'Kontrakt "{kontrakt.kontrakt}" succesvol toegevoegd!', 'success')
        return redirect(url_for('kontrakten.detail', id=kontrakt.id))
    
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    return render_template('add_kontrakt.html', evenementen=evenementen)

@kontrakten_bp.route('/<int:id>')
@login_required
def detail(id):
    kontrakt = Kontrakt.query.get_or_404(id)
    
    # Calculate total bedrag
    total_bedrag = sum(s.facturatiebedrag_incl_btw for s in kontrakt.sponsoringen if s.facturatiebedrag_incl_btw is not None)
    
    return render_template('kontrakt_detail.html', kontrakt=kontrakt, total_bedrag=total_bedrag)

@kontrakten_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@gebruiker_required
def edit(id):
    from flask import request
    from app.models import db
    
    kontrakt = Kontrakt.query.get_or_404(id)
    if request.method == 'POST':
        kontrakt.kontrakt = request.form['kontrakt']
        kontrakt.bedrag = float(request.form['bedrag'])
        kontrakt.tegenprestatie = request.form['tegenprestatie']
        db.session.commit()
        flash('Kontrakt succesvol bijgewerkt!', 'success')
        return redirect(url_for('kontrakten.detail', id=kontrakt.id))
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    return render_template('edit_kontrakt.html', kontrakt=kontrakt, evenementen=evenementen)

@kontrakten_bp.route('/<int:id>/delete', methods=['POST'])
@beheerder_required
def delete(id):
    from app.models import db
    
    kontrakt = Kontrakt.query.get_or_404(id)
    naam = kontrakt.kontrakt
    
    if kontrakt.sponsoringen:
        flash(f'Kontrakt "{naam}" kan niet worden verwijderd omdat er nog sponsoringen aan gekoppeld zijn.', 'error')
        return redirect(url_for('kontrakten.list'))
    
    try:
        db.session.delete(kontrakt)
        db.session.commit()
        flash(f'Kontrakt "{naam}" succesvol verwijderd.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fout bij het verwijderen van kontrakt: {str(e)}', 'error')
        
    return redirect(url_for('kontrakten.list'))

@kontrakten_bp.route('/export/excel')
@login_required
def export_excel():
    flash('Deze functie is nog niet geïmplementeerd in de nieuwe modulaire structuur.', 'warning')
    return redirect(url_for('kontrakten.list'))

@kontrakten_bp.route('/export/pdf')
@login_required
def export_pdf():
    flash('Deze functie is nog niet geïmplementeerd in de nieuwe modulaire structuur.', 'warning')
    return redirect(url_for('kontrakten.list'))
