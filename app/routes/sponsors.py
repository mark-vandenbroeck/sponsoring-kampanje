from flask import Blueprint, render_template, redirect, url_for, flash
from app.utils import login_required, gebruiker_required, beheerder_required
from app.models import Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring

sponsors_bp = Blueprint('sponsors', __name__)

@sponsors_bp.route('/')
@login_required
def list():
    from flask import request
    
    # Get filter parameters
    naam_filter = request.args.get('naam', '')
    kontaktpersoon_filter = request.args.get('kontaktpersoon', '')
    bestuurslid_filter = request.args.get('bestuurslid', '')
    
    # Start with all sponsors
    query = Sponsor.query
    
    # Apply filters
    if naam_filter:
        query = query.filter(Sponsor.naam.ilike(f'%{naam_filter}%'))
    
    if kontaktpersoon_filter:
        query = query.filter(Sponsor.kontaktpersoon.ilike(f'%{kontaktpersoon_filter}%'))
    
    if bestuurslid_filter:
        query = query.filter_by(bestuurslid_id=int(bestuurslid_filter))
    
    sponsors = query.all()
    all_sponsors = Sponsor.query.all()
    bestuursleden = Bestuurslid.query.all()
    
    return render_template('sponsors.html', sponsors=sponsors, all_sponsors=all_sponsors, 
                         bestuursleden=bestuursleden, selected_naam=naam_filter, 
                         selected_kontaktpersoon=kontaktpersoon_filter, 
                         selected_bestuurslid=bestuurslid_filter, 
                         selected_sort='naam', selected_dir='asc')

@sponsors_bp.route('/add', methods=['GET', 'POST'])
@gebruiker_required
def add():
    from flask import request
    from app.models import db
    
    if request.method == 'POST':
        sponsor = Sponsor(
            naam=request.form['naam'],
            kontaktpersoon=request.form.get('kontaktpersoon', ''),
            telefoon=request.form.get('telefoon', ''),
            email=request.form.get('email', ''),
            straat=request.form.get('straat', ''),
            huisnummer=request.form.get('huisnummer', ''),
            postcode=request.form.get('postcode', ''),
            gemeente=request.form.get('gemeente', ''),
            btw_nummer=request.form.get('btw_nummer', ''),
            opmerkingen=request.form.get('opmerkingen', ''),
            bestuurslid_id=int(request.form['bestuurslid_id']) if request.form.get('bestuurslid_id') else None
        )
        db.session.add(sponsor)
        db.session.commit()
        flash(f'Sponsor "{sponsor.naam}" succesvol toegevoegd!', 'success')
        return redirect(url_for('sponsors.detail', id=sponsor.id))
    
    bestuursleden = Bestuurslid.query.order_by(Bestuurslid.naam).all()
    return render_template('add_sponsor.html', bestuursleden=bestuursleden)

@sponsors_bp.route('/<int:id>')
@login_required
def detail(id):
    from flask import request
    
    sponsor = Sponsor.query.get_or_404(id)
    
    # Calculate total bedrag from all sponsoringen for this sponsor
    total_bedrag = sum(
        s.facturatiebedrag_incl_btw for s in sponsor.sponsoringen 
        if s.facturatiebedrag_incl_btw is not None
    )
    
    # Get back URL from referrer or default to list
    back_url = request.referrer or url_for('sponsors.list')
    
    return render_template('sponsor_detail.html', sponsor=sponsor, 
                         total_bedrag=total_bedrag, back_url=back_url)

@sponsors_bp.route('/add-ajax', methods=['POST'])
@gebruiker_required
def add_ajax():
    """AJAX endpoint for adding a new sponsor from modal"""
    from flask import request, jsonify
    from app.models import db
    
    try:
        sponsor = Sponsor(
            naam=request.form['naam'],
            kontaktpersoon=request.form.get('kontaktpersoon', ''),
            telefoon=request.form.get('telefoon', ''),
            email=request.form.get('email', ''),
            straat=request.form.get('straat', ''),
            huisnummer=request.form.get('huisnummer', ''),
            postcode=request.form.get('postcode', ''),
            gemeente=request.form.get('gemeente', ''),
            btw_nummer=request.form.get('btw_nummer', ''),
            opmerkingen=request.form.get('opmerkingen', ''),
            bestuurslid_id=request.form.get('bestuurslid_id') if request.form.get('bestuurslid_id') else None
        )
        db.session.add(sponsor)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sponsor_id': sponsor.id,
            'sponsor_name': sponsor.naam
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@sponsors_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@gebruiker_required
def edit(id):
    from flask import request
    from app.models import db
    
    sponsor = Sponsor.query.get_or_404(id)
    if request.method == 'POST':
        sponsor.naam = request.form['naam']
        sponsor.kontaktpersoon = request.form.get('kontaktpersoon')
        sponsor.telefoon = request.form.get('telefoon')
        sponsor.email = request.form.get('email')
        sponsor.adres = request.form.get('adres')
        sponsor.btw_nummer = request.form.get('btw_nummer')
        sponsor.bestuurslid_id = int(request.form['bestuurslid_id']) if request.form.get('bestuurslid_id') else None
        db.session.commit()
        flash('Sponsor succesvol bijgewerkt!', 'success')
        return redirect(url_for('sponsors.detail', id=sponsor.id))
    bestuursleden = Bestuurslid.query.all()
    return render_template('edit_sponsor.html', sponsor=sponsor, bestuursleden=bestuursleden)

@sponsors_bp.route('/<int:id>/delete', methods=['POST'])
@beheerder_required
def delete(id):
    from app.models import db
    
    sponsor = Sponsor.query.get_or_404(id)
    naam = sponsor.naam
    
    if sponsor.sponsoringen:
        flash(f'Sponsor "{naam}" kan niet worden verwijderd omdat er nog sponsoringen aan gekoppeld zijn.', 'error')
        return redirect(url_for('sponsors.list'))
    
    try:
        db.session.delete(sponsor)
        db.session.commit()
        flash(f'Sponsor "{naam}" succesvol verwijderd.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fout bij het verwijderen van sponsor: {str(e)}', 'error')
        
    return redirect(url_for('sponsors.list'))

@sponsors_bp.route('/export/excel')
@login_required
def export_excel():
    flash('Deze functie is nog niet geïmplementeerd in de nieuwe modulaire structuur.', 'warning')
    return redirect(url_for('sponsors.list'))

@sponsors_bp.route('/export/pdf')
@login_required
def export_pdf():
    flash('Deze functie is nog niet geïmplementeerd in de nieuwe modulaire structuur.', 'warning')
    return redirect(url_for('sponsors.list'))
