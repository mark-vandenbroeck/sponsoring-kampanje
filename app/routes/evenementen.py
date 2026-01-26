from flask import Blueprint, render_template, redirect, url_for, flash
from app.utils import login_required, gebruiker_required, beheerder_required
from app.models import Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring

evenementen_bp = Blueprint('evenementen', __name__)

@evenementen_bp.route('/')
@login_required
def list():
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    return render_template('evenementen.html', evenementen=evenementen, selected_sort='datum', selected_dir='desc')

@evenementen_bp.route('/add', methods=['GET', 'POST'])
@gebruiker_required
def add():
    from flask import request
    from datetime import datetime
    from app.models import db
    
    if request.method == 'POST':
        evenement = Evenement(
            evenementcode=request.form['evenementcode'],
            naam=request.form['naam'],
            datum=datetime.strptime(request.form['datum'], '%Y-%m-%d').date(),
            locatie=request.form['locatie'],
            omschrijving=request.form.get('omschrijving', '')
        )
        db.session.add(evenement)
        db.session.commit()
        flash(f'Evenement "{evenement.naam}" succesvol toegevoegd!', 'success')
        return redirect(url_for('evenementen.detail', id=evenement.id))
    
    return render_template('add_evenement.html')

@evenementen_bp.route('/<int:id>')
@login_required
def detail(id):
    evenement = Evenement.query.get_or_404(id)
    
    # Calculate totals safely
    total_bedrag_incl_btw = sum(s.facturatiebedrag_incl_btw for s in evenement.sponsoringen if s.facturatiebedrag_incl_btw is not None)
    total_bedrag_excl_btw = sum(s.netto_bedrag_excl_btw for s in evenement.sponsoringen if s.netto_bedrag_excl_btw is not None)
    
    return render_template('evenement_detail.html', 
                         evenement=evenement,
                         total_bedrag_incl_btw=total_bedrag_incl_btw,
                         total_bedrag_excl_btw=total_bedrag_excl_btw)

@evenementen_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@gebruiker_required
def edit(id):
    from flask import request
    from datetime import datetime
    from app.models import db
    
    evenement = Evenement.query.get_or_404(id)
    if request.method == 'POST':
        evenement.evenementcode = request.form['evenementcode']
        evenement.naam = request.form['naam']
        evenement.datum = datetime.strptime(request.form['datum'], '%Y-%m-%d').date()
        evenement.locatie = request.form['locatie']
        evenement.omschrijving = request.form['omschrijving']
        db.session.commit()
        flash('Evenement succesvol bijgewerkt!', 'success')
        return redirect(url_for('evenementen.detail', id=evenement.id))
    return render_template('edit_evenement.html', evenement=evenement)

@evenementen_bp.route('/<int:id>/delete', methods=['POST'])
@beheerder_required
def delete(id):
    from app.models import db
    import os
    from flask import current_app
    
    evenement = Evenement.query.get_or_404(id)
    naam = evenement.naam
    
    try:
        # Delete all related sponsoringen first (to handle files and constraints)
        for sponsoring in evenement.sponsoringen:
            # Delete logo files if they exist
            if sponsoring.logo_origineel:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], sponsoring.logo_origineel))
                except:
                    pass
            if sponsoring.logo_afgewerkt_file:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], sponsoring.logo_afgewerkt_file))
                except:
                    pass
            db.session.delete(sponsoring)
        
        # Delete all related kontrakten
        for kontrakt in evenement.kontrakten:
            db.session.delete(kontrakt)
            
        # Delete the evenement
        db.session.delete(evenement)
        db.session.commit()
        
        flash(f'Evenement "{naam}" en alle gerelateerde gegevens succesvol verwijderd.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fout bij het verwijderen van evenement: {str(e)}', 'error')
        
    return redirect(url_for('evenementen.list'))

@evenementen_bp.route('/export/excel')
@login_required
def export_excel():
    import pandas as pd
    import io
    from flask import send_file
    
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    
    data = []
    for e in evenementen:
        data.append({
            'Code': e.evenementcode,
            'Naam': e.naam,
            'Datum': e.datum.strftime('%d/%m/%Y'),
            'Locatie': e.locatie,
            'Omschrijving': e.omschrijving
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Evenementen')
        
        # Adjust column widths
        worksheet = writer.sheets['Evenementen']
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
        download_name='evenementen_export.xlsx'
    )

@evenementen_bp.route('/export/pdf')
@login_required
def export_pdf():
    from xhtml2pdf import pisa
    import io
    from flask import make_response
    from datetime import datetime
    
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    
    html = render_template('evenementen_pdf.html',
                         evenementen=evenementen,
                         current_date=datetime.now().strftime('%d/%m/%Y %H:%M'))
                         
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=evenementen_overzicht.pdf'
        return response
    
    return "Error generating PDF", 500

@evenementen_bp.route('/api/kontrakten/<int:evenement_id>')
@login_required
def api_kontrakten(evenement_id):
    from flask import jsonify
    from app.utils import format_european_currency
    kontrakten = Kontrakt.query.filter_by(evenement_id=evenement_id).all()
    return jsonify([{'id': k.id, 'kontrakt': f"{k.kontrakt} - €{format_european_currency(k.bedrag)}"} for k in kontrakten])

@evenementen_bp.route('/statistieken')
@login_required
def statistieken():
    from app.utils import get_display_amount
    
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    
    # Calculate statistics for each evenement
    evenement_stats = []
    for evenement in evenementen:
        kontrakt_stats = []
        total_excl_btw = 0
        total_incl_btw = 0
        total_betaald = 0
        total_openstaand = 0
        
        for kontrakt in evenement.kontrakten:
            # Calculate totals for this kontrakt
            kontrakt_excl_btw = 0
            kontrakt_incl_btw = 0
            kontrakt_betaald = 0
            kontrakt_openstaand = 0
            
            for sponsoring in kontrakt.sponsoringen:
                # Use fallback logic for excl BTW
                display_amount = get_display_amount(sponsoring)
                kontrakt_excl_btw += display_amount
                
                if sponsoring.facturatiebedrag_incl_btw:
                    kontrakt_incl_btw += sponsoring.facturatiebedrag_incl_btw
                    
                    # Calculate betaald and openstaand
                    if sponsoring.betaald:
                        kontrakt_betaald += sponsoring.facturatiebedrag_incl_btw
                    else:
                        kontrakt_openstaand += sponsoring.facturatiebedrag_incl_btw
            
            if kontrakt_excl_btw > 0 or kontrakt_incl_btw > 0:
                kontrakt_stats.append({
                    'kontrakt': kontrakt.kontrakt,
                    'excl_btw': kontrakt_excl_btw,
                    'incl_btw': kontrakt_incl_btw,
                    'betaald': kontrakt_betaald,
                    'openstaand': kontrakt_openstaand
                })
                total_excl_btw += kontrakt_excl_btw
                total_incl_btw += kontrakt_incl_btw
                total_betaald += kontrakt_betaald
                total_openstaand += kontrakt_openstaand
        
        evenement_stats.append({
            'evenement': evenement,
            'kontrakt_stats': kontrakt_stats,
            'total_excl_btw': total_excl_btw,
            'total_incl_btw': total_incl_btw,
            'total_betaald': total_betaald,
            'total_openstaand': total_openstaand
        })
    
    return render_template('statistieken.html', evenement_stats=evenement_stats)
