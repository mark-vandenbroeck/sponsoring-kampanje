from sqlalchemy import event, inspect
from flask import session
from app.models import AuditLog, Gebruiker, Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring
import json
from datetime import datetime
# ... (imports)

def register_audit_listeners(app, db):
    """
    Registers SQLAlchemy event listeners for auditing changes.
    """
    
    # List of models to audit
    audited_models = [Gebruiker, Evenement, Kontrakt, Sponsor, Bestuurslid, Sponsoring]

    for model in audited_models:
        event.listen(model, 'after_insert', log_insert)
        event.listen(model, 'after_update', log_update)
        event.listen(model, 'after_delete', log_delete)
# ... (register_audit_listeners remains same)

def get_user_info():
    """Helper to safely get current user info from session"""
    try:
        user_id = session.get('user_id')
        if user_id:
            # We try to get the user name from the database
            # Note: This adds a query, but it's essential for the log
            # We could cache this or use session['user_name'] if available
            user = Gebruiker.query.get(user_id)
            if user:
                return user.id, user.email # or user.email
    except:
        pass
    return None, 'System/Unknown'

def log_insert(mapper, connection, target):
    """Log creation of new records"""
    user_id, user_name = get_user_info()
    
    # Get all column values
    state = inspect(target)
    changes = {}
    for attr in state.attrs:
        # Skip internal/large fields if necessary
        if attr.key not in ['logo_origineel', 'logo_afgewerkt_file']:
            changes[attr.key] = [None, attr.value]

    log_entry = {
        'user_id': user_id,
        'user_name': user_name,
        'target_type': target.__class__.__name__,
        'target_id': target.id,
        'action': 'CREATE',
        'changes': json.dumps(changes, default=str),
        'timestamp': datetime.utcnow()
    }
    
    connection.execute(
        AuditLog.__table__.insert(),
        log_entry
    )

def log_update(mapper, connection, target):
    """Log updates to records"""
    user_id, user_name = get_user_info()
    
    state = inspect(target)
    changes = {}
    
    for attr in state.attrs:
        hist = attr.history
        if hist.has_changes():
            old_value = hist.deleted[0] if hist.deleted else None
            new_value = attr.value
            
            # Skip if effectively no change or ignored fields
            if old_value != new_value and attr.key not in ['logo_origineel', 'logo_afgewerkt_file']:
                 changes[attr.key] = [old_value, new_value]

    if not changes:
        return

    log_entry = {
        'user_id': user_id,
        'user_name': user_name,
        'target_type': target.__class__.__name__,
        'target_id': target.id,
        'action': 'UPDATE',
        'changes': json.dumps(changes, default=str),
        'timestamp': datetime.utcnow()
    }
    
    connection.execute(
        AuditLog.__table__.insert(),
        log_entry
    )

def log_delete(mapper, connection, target):
    """Log deletion of records"""
    user_id, user_name = get_user_info()
    
    # Capture final state
    state = inspect(target)
    changes = {}
    for attr in state.attrs:
        if attr.key not in ['logo_origineel', 'logo_afgewerkt_file']:
            changes[attr.key] = [attr.value, None]

    log_entry = {
        'user_id': user_id,
        'user_name': user_name,
        'target_type': target.__class__.__name__,
        'target_id': target.id,
        'action': 'DELETE',
        'changes': json.dumps(changes, default=str),
        'timestamp': datetime.utcnow()
    }
    
    connection.execute(
        AuditLog.__table__.insert(),
        log_entry
    )
