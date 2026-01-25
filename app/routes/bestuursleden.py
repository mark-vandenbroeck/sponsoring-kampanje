from flask import Blueprint, render_template, redirect, url_for, flash
from app.utils import login_required, gebruiker_required, beheerder_required
from app.models import Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring

bestuursleden_bp = Blueprint('bestuursleden', __name__)

@bestuursleden_bp.route('/')
@login_required
def list():
    bestuursleden = Bestuurslid.query.all()
    return render_template('bestuursleden.html', bestuursleden=bestuursleden, selected_sort='naam', selected_dir='asc')

@bestuursleden_bp.route('/add', methods=['GET', 'POST'])
@gebruiker_required
def add():
    from flask import request
    from app.models import db
    
    if request.method == 'POST':
        bestuurslid = Bestuurslid(
            initialen=request.form['initialen'],
            naam=request.form.get('naam', '')
        )
        db.session.add(bestuurslid)
        db.session.commit()
        flash(f'Bestuurslid "{bestuurslid.naam or bestuurslid.initialen}" succesvol toegevoegd!', 'success')
        return redirect(url_for('bestuursleden.detail', id=bestuurslid.id))
    
    return render_template('add_bestuurslid.html')

@bestuursleden_bp.route('/<int:id>')
@login_required
def detail(id):
    bestuurslid = Bestuurslid.query.get_or_404(id)
    # Calculate totals safely to avoid None issues in templates
    total_opgehaald = sum(
        s.facturatiebedrag_incl_btw for s in bestuurslid.sponsoringen if s.facturatiebedrag_incl_btw is not None
    )
    return render_template('bestuurslid_detail.html', bestuurslid=bestuurslid, total_opgehaald=total_opgehaald)

@bestuursleden_bp.route('/add-ajax', methods=['POST'])
@gebruiker_required
def add_ajax():
    """AJAX endpoint for adding a new bestuurslid from modal"""
    from flask import request, jsonify
    from app.models import db
    
    try:
        bestuurslid = Bestuurslid(
            initialen=request.form['initialen'],
            naam=request.form.get('naam', '') if request.form.get('naam') else None
        )
        db.session.add(bestuurslid)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'bestuurslid_id': bestuurslid.id,
            'bestuurslid_name': bestuurslid.naam or bestuurslid.initialen
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@bestuursleden_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@gebruiker_required
def edit(id):
    from flask import request
    from app.models import db
    
    bestuurslid = Bestuurslid.query.get_or_404(id)
    if request.method == 'POST':
        bestuurslid.initialen = request.form['initialen']
        bestuurslid.naam = request.form['naam'] if request.form['naam'] else None
        db.session.commit()
        flash('Bestuurslid succesvol bijgewerkt!', 'success')
        return redirect(url_for('bestuursleden.detail', id=bestuurslid.id))
    return render_template('edit_bestuurslid.html', bestuurslid=bestuurslid)

@bestuursleden_bp.route('/<int:id>/delete', methods=['POST'])
@beheerder_required
def delete(id):
    from app.models import db
    
    bestuurslid = Bestuurslid.query.get_or_404(id)
    naam = bestuurslid.naam or bestuurslid.initialen
    
    if bestuurslid.sponsoringen:
        flash(f'Bestuurslid "{naam}" kan niet worden verwijderd omdat er nog sponsoringen aan gekoppeld zijn.', 'error')
        return redirect(url_for('bestuursleden.list'))
    
    if bestuurslid.sponsors:
        flash(f'Bestuurslid "{naam}" kan niet worden verwijderd omdat er nog sponsors aan gekoppeld zijn.', 'error')
        return redirect(url_for('bestuursleden.list'))
    
    try:
        db.session.delete(bestuurslid)
        db.session.commit()
        flash(f'Bestuurslid "{naam}" succesvol verwijderd.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fout bij het verwijderen van bestuurslid: {str(e)}', 'error')
        
    return redirect(url_for('bestuursleden.list'))

@bestuursleden_bp.route('/export/excel')
@login_required
def export_excel():
    flash('Deze functie is nog niet geïmplementeerd in de nieuwe modulaire structuur.', 'warning')
    return redirect(url_for('bestuursleden.list'))

@bestuursleden_bp.route('/export/pdf')
@login_required
def export_pdf():
    flash('Deze functie is nog niet geïmplementeerd in de nieuwe modulaire structuur.', 'warning')
    return redirect(url_for('bestuursleden.list'))
