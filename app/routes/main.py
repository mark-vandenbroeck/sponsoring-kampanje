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
    """Serve uploaded files"""
    # Get absolute path to upload folder
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
