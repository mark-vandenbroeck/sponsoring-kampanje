from flask import Blueprint, render_template, redirect, url_for, flash
from app.utils import login_required, gebruiker_required, beheerder_required
from app.models import Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring

sponsoringen_bp = Blueprint('sponsoringen', __name__)

@sponsoringen_bp.route('/')
@login_required
def list():
    from flask import request
    
    # Get filter parameters
    evenement_filter = request.args.get('evenement', '')
    kontrakt_filter = request.args.get('kontrakt', '')
    sponsor_filter = request.args.get('sponsor', '')
    logo_bezorgd_filter = request.args.get('logo_bezorgd', '')
    logo_afgewerkt_filter = request.args.get('logo_afgewerkt', '')
    gefactureerd_filter = request.args.get('gefactureerd', '')
    betaald_filter = request.args.get('betaald', '')
    
    # Start with all sponsoringen
    query = Sponsoring.query
    
    # Apply filters
    if evenement_filter:
        query = query.filter_by(evenement_id=int(evenement_filter))
    
    if kontrakt_filter:
        query = query.filter_by(kontrakt_id=int(kontrakt_filter))
    
    if sponsor_filter:
        query = query.filter_by(sponsor_id=int(sponsor_filter))
    
    if logo_bezorgd_filter:
        query = query.filter_by(logo_bezorgd=(logo_bezorgd_filter == '1'))
    
    if logo_afgewerkt_filter:
        query = query.filter_by(logo_afgewerkt=(logo_afgewerkt_filter == '1'))
    
    if gefactureerd_filter:
        query = query.filter_by(gefactureerd=(gefactureerd_filter == '1'))
    
    if betaald_filter:
        query = query.filter_by(betaald=(betaald_filter == '1'))
    
    sponsoringen = query.all()
    
    # Calculate totals
    total_netto_bedrag = sum(
        (s.netto_bedrag_excl_btw or 0) + (s.bedrag_kaarten or 0) 
        for s in sponsoringen
    )
    total_facturatie_bedrag = sum(
        s.facturatiebedrag_incl_btw or 0 
        for s in sponsoringen
    )
    
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    kontrakten = Kontrakt.query.all()
    sponsors = Sponsor.query.all()
    
    return render_template('sponsoringen.html', sponsoringen=sponsoringen, 
                         evenementen=evenementen, kontrakten=kontrakten, sponsors=sponsors, 
                         selected_evenement=evenement_filter, selected_kontrakt=kontrakt_filter, 
                         selected_sponsor=sponsor_filter,
                         selected_logo_bezorgd=logo_bezorgd_filter, 
                         selected_logo_afgewerkt=logo_afgewerkt_filter, 
                         selected_gefactureerd=gefactureerd_filter, 
                         selected_betaald=betaald_filter,
                         selected_sort='evenement', selected_dir='asc', 
                         total_netto_bedrag=total_netto_bedrag, 
                         total_facturatie_bedrag=total_facturatie_bedrag)

@sponsoringen_bp.route('/add', methods=['GET', 'POST'])
@gebruiker_required
def add():
    from flask import request
    from app.models import db
    import os
    from werkzeug.utils import secure_filename
    from flask import current_app
    
    if request.method == 'POST':
        # Handle file uploads
        logo_origineel = None
        logo_afgewerkt_file = None
        
        if 'logo_origineel' in request.files:
            file = request.files['logo_origineel']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                logo_origineel = filename
        
        if 'logo_afgewerkt_file' in request.files:
            file = request.files['logo_afgewerkt_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                logo_afgewerkt_file = filename

        sponsoring = Sponsoring(
            evenement_id=int(request.form['evenement_id']),
            kontrakt_id=int(request.form['kontrakt_id']),
            sponsor_id=int(request.form['sponsor_id']),
            aangebracht_door_id=int(request.form['aangebracht_door_id']),
            bedrag_kaarten=float(request.form['bedrag_kaarten']) if request.form.get('bedrag_kaarten') else None,
            netto_bedrag_excl_btw=float(request.form['netto_bedrag_excl_btw']) if request.form.get('netto_bedrag_excl_btw') else None,
            facturatiebedrag_incl_btw=float(request.form['facturatiebedrag_incl_btw']) if request.form.get('facturatiebedrag_incl_btw') else None,
            gefactureerd='gefactureerd' in request.form,
            betaald='betaald' in request.form,
            logo_bezorgd=bool(logo_origineel),
            logo_afgewerkt=bool(logo_afgewerkt_file),
            logo_origineel=logo_origineel,
            logo_afgewerkt_file=logo_afgewerkt_file,
            opmerkingen=request.form.get('opmerkingen', '')
        )
        db.session.add(sponsoring)
        db.session.commit()
        flash('Sponsoring succesvol toegevoegd!', 'success')
        return redirect(url_for('sponsoringen.detail', id=sponsoring.id))
    
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    kontrakten = Kontrakt.query.all()
    sponsors = Sponsor.query.order_by(Sponsor.naam).all()
    bestuursleden = Bestuurslid.query.order_by(Bestuurslid.naam).all()
    
    return render_template('add_sponsoring.html', 
                         evenementen=evenementen, 
                         kontrakten=kontrakten, 
                         sponsors=sponsors, 
                         bestuursleden=bestuursleden)

@sponsoringen_bp.route('/<int:id>')
@login_required
def detail(id):
    from app.utils import get_display_amount
    from flask import request
    
    sponsoring = Sponsoring.query.get_or_404(id)
    display_amount = get_display_amount(sponsoring)
    
    # Get back URL from referrer or default to list
    back_url = request.referrer or url_for('sponsoringen.list')
    
    return render_template('sponsoring_detail.html', sponsoring=sponsoring, 
                         display_amount=display_amount, back_url=back_url)

@sponsoringen_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@gebruiker_required
def edit(id):
    from flask import request
    from app.models import db
    import os
    from werkzeug.utils import secure_filename
    from flask import current_app
    
    sponsoring = Sponsoring.query.get_or_404(id)
    if request.method == 'POST':
        sponsoring.evenement_id = int(request.form['evenement_id'])
        sponsoring.kontrakt_id = int(request.form['kontrakt_id'])
        sponsoring.sponsor_id = int(request.form['sponsor_id'])
        sponsoring.aangebracht_door_id = int(request.form['aangebracht_door_id'])
        
        # Handle numeric fields
        sponsoring.bedrag_kaarten = float(request.form['bedrag_kaarten']) if request.form.get('bedrag_kaarten') else None
        sponsoring.netto_bedrag_excl_btw = float(request.form['netto_bedrag_excl_btw']) if request.form.get('netto_bedrag_excl_btw') else None
        sponsoring.facturatiebedrag_incl_btw = float(request.form['facturatiebedrag_incl_btw']) if request.form.get('facturatiebedrag_incl_btw') else None
        
        # Handle boolean fields
        sponsoring.gefactureerd = 'gefactureerd' in request.form
        sponsoring.betaald = 'betaald' in request.form
        sponsoring.logo_bezorgd = 'logo_bezorgd' in request.form
        sponsoring.logo_afgewerkt = 'logo_afgewerkt' in request.form
        
        sponsoring.opmerkingen = request.form.get('opmerkingen')
        
        # Handle file uploads
        if 'logo_origineel' in request.files:
            file = request.files['logo_origineel']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                sponsoring.logo_origineel = filename
        
        if 'logo_afgewerkt_file' in request.files:
            file = request.files['logo_afgewerkt_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                sponsoring.logo_afgewerkt_file = filename
        
        db.session.commit()
        flash('Sponsoring succesvol bijgewerkt!', 'success')
        return redirect(url_for('sponsoringen.detail', id=sponsoring.id))
    
    evenementen = Evenement.query.order_by(Evenement.datum.desc()).all()
    kontrakten = Kontrakt.query.all()
    sponsors = Sponsor.query.all()
    bestuursleden = Bestuurslid.query.all()
    return render_template('edit_sponsoring.html', sponsoring=sponsoring, 
                         evenementen=evenementen, kontrakten=kontrakten, 
                         sponsors=sponsors, bestuursleden=bestuursleden)

@sponsoringen_bp.route('/<int:id>/delete', methods=['POST'])
@beheerder_required
def delete(id):
    from app.models import db
    import os
    from flask import current_app
    
    sponsoring = Sponsoring.query.get_or_404(id)
    
    try:
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
        db.session.commit()
        flash('Sponsoring succesvol verwijderd.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fout bij het verwijderen van sponsoring: {str(e)}', 'error')
        
    return redirect(url_for('sponsoringen.list'))

@sponsoringen_bp.route('/export/excel')
@login_required
def export_excel():
    import pandas as pd
    import io
    from flask import send_file
    from app.utils import get_display_amount
    
    # Query all sponsorings with related data
    sponsorings = Sponsoring.query.join(Evenement).join(Sponsor).join(Kontrakt, Sponsoring.kontrakt_id == Kontrakt.id).order_by(Evenement.datum.desc(), Sponsor.naam).all()
    
    # Prepare data for DataFrame
    data = []
    for s in sponsorings:
        data.append({
            'Evenement': s.evenement.naam,
            'Datum': s.evenement.datum.strftime('%d/%m/%Y'),
            'Sponsor': s.sponsor.naam,
            'Kontrakt': s.kontrakt.kontrakt,
            'Aangebracht door': s.aangebracht_door.naam if s.aangebracht_door else '',
            'Bedrag Kaarten': s.bedrag_kaarten or 0,
            'Bedrag Excl BTW': s.netto_bedrag_excl_btw or 0,
            'Totaal': get_display_amount(s),
            'Status': 'Betaald' if s.betaald else ('Gefactureerd' if s.gefactureerd else 'In behandeling'),
            'Logo Origineel': 'Ja' if s.logo_origineel else 'Nee',
            'Logo Afgewerkt': 'Ja' if s.logo_afgewerkt_file else 'Nee'
        })
    
    df = pd.DataFrame(data)
    
    # Create BytesIO object
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sponsoringen')
        
        # Adjust column widths
        worksheet = writer.sheets['Sponsoringen']
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
        download_name='sponsoringen_export.xlsx'
    )

@sponsoringen_bp.route('/export/pdf')
@login_required
def export_pdf():
    from xhtml2pdf import pisa
    import io
    from flask import make_response
    from datetime import datetime
    from app.utils import get_display_amount
    
    sponsorings = Sponsoring.query.join(Evenement).join(Sponsor).join(Kontrakt, Sponsoring.kontrakt_id == Kontrakt.id)\
        .order_by(Evenement.datum.desc(), Sponsor.naam).all()
        
    html = render_template('sponsoring_pdf.html', 
                         sponsorings=sponsorings,
                         get_display_amount=get_display_amount,
                         current_date=datetime.now().strftime('%d/%m/%Y %H:%M'))
                         
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=sponsoringen_overzicht.pdf'
        return response
    
    return "Error generating PDF", 500

@sponsoringen_bp.route('/download-logos')
@login_required
def download_logos():
    import zipfile
    import io
    import os
    from flask import send_file, current_app
    from werkzeug.utils import secure_filename
    
    sponsorings = Sponsoring.query.filter(
        (Sponsoring.logo_origineel != None) | 
        (Sponsoring.logo_afgewerkt_file != None)
    ).all()
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for s in sponsorings:
            # Use secure filenames for the directory structure in zip
            sponsor_name = secure_filename(s.sponsor.naam)
            evenement_name = secure_filename(s.evenement.naam)
            base_path = f"{evenement_name}/{sponsor_name}"
            
            # Helper to add file
            def add_logo(filename, type_name):
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    # Get the extension
                    ext = os.path.splitext(filename)[1]
                    # Create a nice name for inside the zip
                    zip_name = f"{base_path}/{type_name}{ext}"
                    zf.write(file_path, zip_name)
            
            if s.logo_origineel:
                add_logo(s.logo_origineel, "logo_origineel")
                
            if s.logo_afgewerkt_file:
                add_logo(s.logo_afgewerkt_file, "logo_afgewerkt")
                
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='logos_export.zip'
    )
