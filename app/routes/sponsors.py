from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.utils import login_required, gebruiker_required, beheerder_required
from app.models import Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring

sponsors_bp = Blueprint('sponsors', __name__)

@sponsors_bp.route('/')
@login_required
def list():
    # Define keys to persist
    filter_keys = ['naam', 'kontaktpersoon', 'bestuurslid']

    # Handle reset
    if request.args.get('reset'):
        if 'sponsor_filters' in session:
            session.pop('sponsor_filters')
        return redirect(url_for('sponsors.list'))

    # Check if request has any relevant args
    has_filter_args = any(key in request.args for key in filter_keys)

    if has_filter_args:
        # Save to session
        filters = {k: request.args.get(k) for k in filter_keys if request.args.get(k) is not None}
        session['sponsor_filters'] = filters
    else:
        # No args provided, try to load from session
        if 'sponsor_filters' in session:
            return redirect(url_for('sponsors.list', **session['sponsor_filters']))
            
    # Get filter parameters (now prioritized from request args, which might be populated from session via redirect)
    naam_filter = request.args.get('naam', '')
    kontaktpersoon_filter = request.args.get('kontaktpersoon', '')
    bestuurslid_filter = request.args.get('bestuurslid', '')
    
    # Sort parameters
    sort = request.args.get('sort', 'naam')
    direction = request.args.get('dir', 'asc')
    
    # Start with all sponsors
    query = Sponsor.query
    
    # Apply filters
    if naam_filter:
        query = query.filter(Sponsor.naam.ilike(f'%{naam_filter}%'))
    
    if kontaktpersoon_filter:
        query = query.filter(Sponsor.kontaktpersoon.ilike(f'%{kontaktpersoon_filter}%'))
    
    if bestuurslid_filter:
        try:
            query = query.filter_by(bestuurslid_id=int(bestuurslid_filter))
        except ValueError:
            pass # Ignore invalid bestuurslid_id

    # Apply sorting
    if sort == 'naam':
        if direction == 'desc':
            query = query.order_by(Sponsor.naam.desc())
        else:
            query = query.order_by(Sponsor.naam.asc())
            
    elif sort == 'kontaktpersoon':
        if direction == 'desc':
            query = query.order_by(Sponsor.kontaktpersoon.desc())
        else:
            query = query.order_by(Sponsor.kontaktpersoon.asc())
            
    elif sort == 'telefoon':
        if direction == 'desc':
            query = query.order_by(Sponsor.telefoon.desc())
        else:
            query = query.order_by(Sponsor.telefoon.asc())
            
    elif sort == 'email':
        if direction == 'desc':
            query = query.order_by(Sponsor.email.desc())
        else:
            query = query.order_by(Sponsor.email.asc())
            
    elif sort == 'bestuurslid':
        query = query.join(Bestuurslid)
        if direction == 'desc':
            query = query.order_by(Bestuurslid.naam.desc())
        else:
            query = query.order_by(Bestuurslid.naam.asc())
            
    elif sort == 'sponsoringen':
        # Sort by number of sponsorships
        from sqlalchemy import func
        subquery = db.session.query(Sponsoring.sponsor_id, func.count('*').label('count')).group_by(Sponsoring.sponsor_id).subquery()
        query = query.outerjoin(subquery, Sponsor.id == subquery.c.sponsor_id)
        if direction == 'desc':
            query = query.order_by(subquery.c.count.desc())
        else:
            query = query.order_by(subquery.c.count.asc())
    
    sponsors = query.all()
    all_sponsors = Sponsor.query.all()
    bestuursleden = Bestuurslid.query.all()
    
    return render_template('sponsors.html', sponsors=sponsors, all_sponsors=all_sponsors, 
                           bestuursleden=bestuursleden, selected_naam=naam_filter, 
                           selected_kontaktpersoon=kontaktpersoon_filter, 
                           selected_bestuurslid=bestuurslid_filter,
                           selected_sort=sort, selected_dir=direction)

@sponsors_bp.route('/add', methods=['GET', 'POST'])
@gebruiker_required
def add():
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
    import pandas as pd
    import io
    from flask import send_file
    
    sponsors = Sponsor.query.order_by(Sponsor.naam).all()
    
    data = []
    for s in sponsors:
        data.append({
            'Naam': s.naam,
            'Contactpersoon': s.kontaktpersoon,
            'Email': s.email,
            'Telefoon': s.telefoon,
            'Straat': s.straat,
            'Huisnummer': s.huisnummer,
            'Postcode': s.postcode,
            'Gemeente': s.gemeente,
            'BTW Nummer': s.btw_nummer,
            'Opmerkingen': s.opmerkingen,
            'Aanbrenger': s.bestuurslid.naam if s.bestuurslid else ''
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sponsors')
        
        # Adjust column widths
        worksheet = writer.sheets['Sponsors']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_len
            
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sponsors_export.xlsx'
    )

@sponsors_bp.route('/export/pdf')
@login_required
def export_pdf():
    from xhtml2pdf import pisa
    import io
    from flask import make_response
    from datetime import datetime
    
    sponsors = Sponsor.query.order_by(Sponsor.naam).all()
    
    html = render_template('sponsors_pdf.html',
                         sponsors=sponsors,
                         current_date=datetime.now().strftime('%d/%m/%Y %H:%M'))
                         
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=sponsors_overzicht.pdf'
        return response
    
    return "Error generating PDF", 500
