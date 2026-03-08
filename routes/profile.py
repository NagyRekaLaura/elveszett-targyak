from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_user, current_user, login_required
from database import db, User, Attachment
from werkzeug.utils import secure_filename
import os
from datetime import datetime

profile_routes = Blueprint("profile", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/attachments'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_routes.route('/profile', defaults={'user_id': None})
@profile_routes.route('/profile/<int:user_id>')
def profile(user_id):
    print(user_id)
    if user_id is None:
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        user = current_user
    else:
        user = User.query.get(user_id)
        if user is None:
            return redirect(url_for('main.home'))
    print(user.id)
    return render_template("profile.html", user=user)


@profile_routes.route('/createprofile', methods=['GET', 'POST'])
@login_required
def createprofile():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            address = request.form.get('address', '').strip()
            birthdate_str = request.form.get('birthdate', '').strip()
            
            if not name:
                return jsonify({
                    'success': False,
                    'error': 'A megjelenítendő név megadása kötelező!'
                }), 400
            
            if not address:
                return jsonify({
                    'success': False,
                    'error': 'A lakhely megadása kötelező!'
                }), 400
            
            if not birthdate_str:
                return jsonify({
                    'success': False,
                    'error': 'A születési idő megadása kötelező!'
                }), 400
            
            current_user.name = name
            current_user.phone_number = request.form.get('phone_number', '').strip()
            current_user.phone_number_is_private = request.form.get('phone_number_is_private') == 'true'
            current_user.address = address
            current_user.address_is_private = request.form.get('address_is_private') == 'true'
            
            try:
                current_user.birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Érvénytelen születési idő formátum!'
                }), 400
            
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    
                    file.save(filepath)
                    
                    attachment = Attachment(
                        filename=filename
                    )
                    db.session.add(attachment)
                    db.session.flush()
                    current_user.profile_picture = attachment.id
            
            enable_2fa = request.form.get('2fa_enabled') == 'true'
            if enable_2fa and not current_user._2fa_enabled:
                current_user._2fa_enabled = True
            
            # Adatbázisba mentés
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profil sikeresen frissítve!'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Hiba a profil frissítésénél: {str(e)}'
            }), 400
    
    return render_template("createprofile.html", user=current_user)
