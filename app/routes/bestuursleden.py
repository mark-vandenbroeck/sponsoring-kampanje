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
        flash(f'Aanbrenger "{bestuurslid.naam or bestuurslid.initialen}" succesvol toegevoegd!', 'success')
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
        flash('Aanbrenger succesvol bijgewerkt!', 'success')
        return redirect(url_for('bestuursleden.detail', id=bestuurslid.id))
    return render_template('edit_bestuurslid.html', bestuurslid=bestuurslid)

@bestuursleden_bp.route('/<int:id>/delete', methods=['POST'])
@beheerder_required
def delete(id):
    from app.models import db
    
    bestuurslid = Bestuurslid.query.get_or_404(id)
    naam = bestuurslid.naam or bestuurslid.initialen
    
    if bestuurslid.sponsoringen:
        flash(f'Aanbrenger "{naam}" kan niet worden verwijderd omdat er nog sponsoringen aan gekoppeld zijn.', 'error')
        return redirect(url_for('bestuursleden.list'))
    
    if bestuurslid.sponsors:
        flash(f'Aanbrenger "{naam}" kan niet worden verwijderd omdat er nog sponsors aan gekoppeld zijn.', 'error')
        return redirect(url_for('bestuursleden.list'))
    
    try:
        db.session.delete(bestuurslid)
        db.session.commit()
        flash(f'Aanbrenger "{naam}" succesvol verwijderd.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fout bij het verwijderen van aanbrenger: {str(e)}', 'error')
        
    return redirect(url_for('bestuursleden.list'))

@bestuursleden_bp.route('/export/excel')
@login_required
def export_excel():
    import pandas as pd
    import io
    from flask import send_file
    
    bestuursleden = Bestuurslid.query.order_by(Bestuurslid.naam).all()
    
    data = []
    for b in bestuursleden:
        # Calculate totals safely
        total_opgehaald = sum(
            s.facturatiebedrag_incl_btw for s in b.sponsoringen if s.facturatiebedrag_incl_btw is not None
        )
        
        data.append({
            'Initialen': b.initialen,
            'Naam': b.naam,
            'Totaal Opgehaald': total_opgehaald
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Aanbrengers')
        
        # Adjust column widths
        worksheet = writer.sheets['Aanbrengers']
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
        download_name='bestuursleden_export.xlsx'
    )

@bestuursleden_bp.route('/export/pdf')
@login_required
def export_pdf():
    from xhtml2pdf import pisa
    import io
    from flask import make_response
    from datetime import datetime
    
    bestuursleden = Bestuurslid.query.order_by(Bestuurslid.naam).all()
    
    html = render_template('bestuursleden_pdf.html',
                         bestuursleden=bestuursleden,
                         current_date=datetime.now().strftime('%d/%m/%Y %H:%M'))
                         
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=bestuursleden_overzicht.pdf'
        return response
    
    return "Error generating PDF", 500
