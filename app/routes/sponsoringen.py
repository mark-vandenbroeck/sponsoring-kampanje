from flask import Blueprint, render_template, redirect, url_for, flash
from app.utils import login_required, gebruiker_required, beheerder_required
from app.models import Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring

sponsoringen_bp = Blueprint('sponsoringen', __name__)

@sponsoringen_bp.route('/')
@login_required
def list():
    from flask import request, session
    
    # Handle reset
    if request.args.get('reset'):
        if 'sponsoring_filters' in session:
            session.pop('sponsoring_filters')
        return redirect(url_for('sponsoringen.list'))
        
    # Define keys to persist
    filter_keys = ['evenement', 'kontrakt', 'sponsor', 'logo_bezorgd', 
                   'logo_afgewerkt', 'gefactureerd', 'betaald', 'sort', 'dir']
    
    # Check if request has any relevant args (excluding pagination if we had it, but mostly filters)
    # We check if ANY of the filter keys are in request.args
    has_filter_args = any(key in request.args for key in filter_keys)
    
    if has_filter_args:
        # Save to session
        # We save all present keys. Empty strings mean "filter by nothing" which is effectively clearing that specific filter.
        # But wait, if I select "Alle" in dropdown, it sends key="".
        # If I don't include it in session, next time we load from session, we might load an old value?
        # No, "has_filter_args" is true even if key is present but empty.
        # So we should overwrite session with current state.
        filters = {k: request.args.get(k) for k in filter_keys if k in request.args}
        session['sponsoring_filters'] = filters
    else:
        # No args provided, try to load from session
        if 'sponsoring_filters' in session:
            return redirect(url_for('sponsoringen.list', **session['sponsoring_filters']))
    
    # Get filter parameters (now populated from args whether direct or redirected)
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
        try:
            query = query.filter_by(sponsor_id=int(sponsor_filter))
        except ValueError:
            pass # Ignore invalid sponsor filter
    
    if logo_bezorgd_filter:
        query = query.filter_by(logo_bezorgd=(logo_bezorgd_filter == 'ja'))
    
    if logo_afgewerkt_filter:
        query = query.filter_by(logo_afgewerkt=(logo_afgewerkt_filter == 'ja'))
    
    if gefactureerd_filter:
        query = query.filter_by(gefactureerd=(gefactureerd_filter == 'ja'))
    
    if betaald_filter:
        query = query.filter_by(betaald=(betaald_filter == 'ja'))
    
    # Sorting logic
    sort = request.args.get('sort', 'evenement')
    direction = request.args.get('dir', 'asc')
    
    if sort == 'evenement':
        if direction == 'asc':
            query = query.join(Evenement).order_by(Evenement.datum.asc())
        else:
            query = query.join(Evenement).order_by(Evenement.datum.desc())
    elif sort == 'kontrakt':
        if direction == 'asc':
            query = query.join(Kontrakt).order_by(Kontrakt.kontrakt.asc())
        else:
            query = query.join(Kontrakt).order_by(Kontrakt.kontrakt.desc())
    elif sort == 'sponsor':
        if direction == 'asc':
            query = query.join(Sponsor).order_by(Sponsor.naam.asc())
        else:
            query = query.join(Sponsor).order_by(Sponsor.naam.desc())
    elif sort == 'aangebracht':
        if direction == 'asc':
            query = query.join(Bestuurslid, Sponsoring.aangebracht_door_id == Bestuurslid.id).order_by(Bestuurslid.naam.asc())
        else:
            query = query.join(Bestuurslid, Sponsoring.aangebracht_door_id == Bestuurslid.id).order_by(Bestuurslid.naam.desc())
    # Note: Sorting by amount is done in Python because it's a computed property, or we sort normally if it's a column
    # If we need complex sorting, we might stick to default (Evenement desc) or handle simple cases.
    # The existing code didn't safeguard lines 22-72 logic completely, I'm replacing the block.
    
    sponsoringen = query.all()
    
    # Python-side sorting for computed fields if complex, but simple join sorting handled above.
    if sort == 'bedrag':
        sponsoringen.sort(key=lambda s: (s.netto_bedrag_excl_btw or 0) + (s.bedrag_kaarten or 0), reverse=(direction == 'desc'))
    elif sort == 'bedrag_incl':
        sponsoringen.sort(key=lambda s: s.facturatiebedrag_incl_btw or 0, reverse=(direction == 'desc'))
    
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
                         selected_sort=sort, selected_dir=direction, 
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
        
        if 'logo_afgewerkt' in request.files:
            file = request.files['logo_afgewerkt']
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
    back_url = request.referrer
    if not back_url or '/edit' in back_url:
        back_url = url_for('sponsoringen.list')
    
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
        if 'evenement_id' in request.form:
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
        # Logo status wordt automatisch bepaald door aanwezigheid bestanden
        
        sponsoring.opmerkingen = request.form.get('opmerkingen')
        
        # Handle file uploads
        if 'logo_origineel' in request.files:
            file = request.files['logo_origineel']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                sponsoring.logo_origineel = filename
        
        if 'logo_afgewerkt' in request.files:
            file = request.files['logo_afgewerkt']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                sponsoring.logo_afgewerkt_file = filename
        
        # Update boolean flags based on file presence
        sponsoring.logo_bezorgd = bool(sponsoring.logo_origineel)
        sponsoring.logo_afgewerkt = bool(sponsoring.logo_afgewerkt_file)
        
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
    from flask import send_file, session, request
    from app.utils import get_display_amount
    
    # Retrieve filters: check request.args first (URL), then session
    session_filters = session.get('sponsoring_filters', {})
    
    def get_filter(key):
        # Priority: URL arg -> Session -> None
        return request.args.get(key) or session_filters.get(key)
    
    # Start with all sponsoringen
    query = Sponsoring.query
    
    # Apply filters
    if get_filter('evenement'):
        query = query.filter_by(evenement_id=int(get_filter('evenement')))
    
    if get_filter('kontrakt'):
        query = query.filter_by(kontrakt_id=int(get_filter('kontrakt')))
    
    if get_filter('sponsor'):
        try:
            query = query.filter_by(sponsor_id=int(get_filter('sponsor')))
        except ValueError:
            pass
            
    if get_filter('logo_bezorgd'):
        query = query.filter_by(logo_bezorgd=(get_filter('logo_bezorgd') == 'ja'))
        
    if get_filter('logo_afgewerkt'):
        query = query.filter_by(logo_afgewerkt=(get_filter('logo_afgewerkt') == 'ja'))
        
    if get_filter('gefactureerd'):
        query = query.filter_by(gefactureerd=(get_filter('gefactureerd') == 'ja'))
        
    if get_filter('betaald'):
        query = query.filter_by(betaald=(get_filter('betaald') == 'ja'))
        
    # Apply sorting (default to Evenement desc, Sponsor asc)
    query = query.join(Evenement).join(Sponsor).join(Kontrakt, Sponsoring.kontrakt_id == Kontrakt.id).order_by(Evenement.datum.desc(), Sponsor.naam)
    
    sponsorings = query.all()
    
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
    from flask import make_response, session, request
    from datetime import datetime
    from app.utils import get_display_amount
    
    # Retrieve filters: check request.args first (URL), then session
    session_filters = session.get('sponsoring_filters', {})
    
    def get_filter(key):
        # Priority: URL arg -> Session -> None
        return request.args.get(key) or session_filters.get(key)
    
    # Start with all sponsoringen
    query = Sponsoring.query
    
    # Apply filters
    if get_filter('evenement'):
        query = query.filter_by(evenement_id=int(get_filter('evenement')))
    
    if get_filter('kontrakt'):
        query = query.filter_by(kontrakt_id=int(get_filter('kontrakt')))
    
    if get_filter('sponsor'):
        try:
            query = query.filter_by(sponsor_id=int(get_filter('sponsor')))
        except ValueError:
            pass
            
    if get_filter('logo_bezorgd'):
        query = query.filter_by(logo_bezorgd=(get_filter('logo_bezorgd') == 'ja'))
        
    if get_filter('logo_afgewerkt'):
        query = query.filter_by(logo_afgewerkt=(get_filter('logo_afgewerkt') == 'ja'))
        
    if get_filter('gefactureerd'):
        query = query.filter_by(gefactureerd=(get_filter('gefactureerd') == 'ja'))
        
    if get_filter('betaald'):
        query = query.filter_by(betaald=(get_filter('betaald') == 'ja'))
    
    # Default sort
    query = query.join(Evenement).join(Sponsor).join(Kontrakt, Sponsoring.kontrakt_id == Kontrakt.id).order_by(Evenement.datum.desc(), Sponsor.naam)
    
    sponsorings = query.all()
        
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
    from flask import send_file, current_app, request
    from werkzeug.utils import secure_filename
    
    # Get filter parameters matching list route
    evenement_filter = request.args.get('evenement', '')
    kontrakt_filter = request.args.get('kontrakt', '')
    sponsor_filter = request.args.get('sponsor', '')
    logo_bezorgd_filter = request.args.get('logo_bezorgd', '')
    logo_afgewerkt_filter = request.args.get('logo_afgewerkt', '')
    gefactureerd_filter = request.args.get('gefactureerd', '')
    betaald_filter = request.args.get('betaald', '')
    
    query = Sponsoring.query
    
    # Apply filters
    if evenement_filter:
        query = query.filter_by(evenement_id=int(evenement_filter))
    if kontrakt_filter:
        query = query.filter_by(kontrakt_id=int(kontrakt_filter))
    if sponsor_filter:
        try:
            query = query.filter_by(sponsor_id=int(sponsor_filter))
        except ValueError:
            pass
    if logo_bezorgd_filter:
        query = query.filter_by(logo_bezorgd=(logo_bezorgd_filter == 'ja'))
    if logo_afgewerkt_filter:
        query = query.filter_by(logo_afgewerkt=(logo_afgewerkt_filter == 'ja'))
    if gefactureerd_filter:
        query = query.filter_by(gefactureerd=(gefactureerd_filter == 'ja'))
    if betaald_filter:
        query = query.filter_by(betaald=(betaald_filter == 'ja'))
        
    # Only get sponsorings that actually have a finished logo
    query = query.filter(Sponsoring.logo_afgewerkt_file != None)
    
    sponsorings = query.all()
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for s in sponsorings:
            # Use secure filenames for the directory structure in zip
            sponsor_name = secure_filename(s.sponsor.naam)
            evenement_name = secure_filename(s.evenement.naam)
            
            # Directory per evenement, file per sponsor
            base_path = f"{evenement_name}"
            
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], s.logo_afgewerkt_file)
            if os.path.exists(file_path):
                # Get the extension
                ext = os.path.splitext(s.logo_afgewerkt_file)[1]
                # Create a nice name for inside the zip: Event/SponsorName.ext
                zip_name = f"{base_path}/{sponsor_name}{ext}"
                zf.write(file_path, zip_name)
                
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='afgewerkte_logos_export.zip'
    )
