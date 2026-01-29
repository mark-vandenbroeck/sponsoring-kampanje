from flask import Blueprint, render_template, request
from app.utils import beheerder_required
from app.models import AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@beheerder_required
def list():
    from app.models import db
    from datetime import datetime
    
    page = request.args.get('page', 1, type=int)
    
    # Filter parameters
    action = request.args.get('action')
    target_type = request.args.get('target_type')
    user_id = request.args.get('user_id', type=int)
    search = request.args.get('search')
    date_start = request.args.get('date_start')
    date_end = request.args.get('date_end')
    
    query = AuditLog.query
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
        
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
        
    if date_start:
        try:
            ds = datetime.strptime(date_start, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= ds)
        except ValueError:
            pass
            
    if date_end:
        try:
            de = datetime.strptime(date_end, '%Y-%m-%d')
            # Add one day to include the end date fully
            de = de.replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.timestamp <= de)
        except ValueError:
            pass

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                AuditLog.user_name.ilike(search_term),
                AuditLog.target_type.ilike(search_term),
                # Note: valid only if DB supports casting JSON to string easily or if it's stored as string
                db.cast(AuditLog.changes, db.String).ilike(search_term) 
            )
        )
            
    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    target_types = sorted(['Sponsor', 'Sponsoring', 'Evenement', 'Kontrakt', 'Gebruiker', 'Bestuurslid'])
    
    return render_template('audit_list.html', 
                         logs=pagination.items, 
                         pagination=pagination,
                         target_types=target_types)
