from flask import Blueprint, redirect, url_for, send_from_directory, current_app
from app.utils import login_required
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login page"""
    from flask import session
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded files from database or fallback to local storage"""
    from app.models import Sponsoring
    from flask import send_file
    import io
    
    # 1. Check if this is a request for a thumbnail
    if filename.endswith('_thumb.png'):
        base_name = filename[:-10]  # strip '_thumb.png'
        
        # Find record where original or finished filename starts with this base name
        sponsoring = Sponsoring.query.filter(
            (Sponsoring.logo_origineel.like(f"{base_name}%")) |
            (Sponsoring.logo_afgewerkt_file.like(f"{base_name}%"))
        ).first()
        
        if sponsoring:
            # Determine which thumbnail to serve
            if sponsoring.logo_origineel and sponsoring.logo_origineel.startswith(base_name) and sponsoring.logo_origineel_thumb_data:
                return send_file(io.BytesIO(sponsoring.logo_origineel_thumb_data), mimetype='image/png', download_name=filename)
            elif sponsoring.logo_afgewerkt_file and sponsoring.logo_afgewerkt_file.startswith(base_name) and sponsoring.logo_afgewerkt_thumb_data:
                return send_file(io.BytesIO(sponsoring.logo_afgewerkt_thumb_data), mimetype='image/png', download_name=filename)
    
    # 2. Check if this is a request for the original or finished file
    sponsoring = Sponsoring.query.filter(
        (Sponsoring.logo_origineel == filename) |
        (Sponsoring.logo_afgewerkt_file == filename)
    ).first()
    
    if sponsoring:
        if sponsoring.logo_origineel == filename and sponsoring.logo_origineel_data:
            mime = sponsoring.logo_origineel_mime or 'application/octet-stream'
            return send_file(io.BytesIO(sponsoring.logo_origineel_data), mimetype=mime, download_name=filename)
        elif sponsoring.logo_afgewerkt_file == filename and sponsoring.logo_afgewerkt_data:
            mime = sponsoring.logo_afgewerkt_mime or 'application/octet-stream'
            return send_file(io.BytesIO(sponsoring.logo_afgewerkt_data), mimetype=mime, download_name=filename)
            
    # 3. Fallback to local filesystem if not found in database
    upload_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        current_app.config['UPLOAD_FOLDER']
    )
    return send_from_directory(upload_folder, filename)

@main_bp.route('/handleiding')
@login_required
def handleiding():
    """Show user manual"""
    from flask import render_template
    return render_template('handleiding.html')
