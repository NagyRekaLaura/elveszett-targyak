from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from flask_login import login_user, current_user, login_required
from database import TwoFactorAuth, db, User, Attachment, Item, Reports
from werkzeug.utils import secure_filename
import os
from datetime import datetime

profile_routes = Blueprint("profile", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/attachments'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_profile_picture_url(user):
    if not user.profile_picture:
        return None

    attachment = Attachment.query.get(user.profile_picture)
    if not attachment:
        return None

    return f"attachments/{attachment.filename}"


def _normalize_language(language_value):
    language_value = (language_value or '').strip().lower()
    return 'en' if language_value.startswith('en') else 'hu'


def _localized_description(item, language):
    if language == 'en':
        return item.description_en or item.description_hu or ''
    return item.description_hu or item.description_en or ''


def _save_profile_form(user):
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

    user.name = name
    user.phone_number = request.form.get('phone_number', '').strip()
    user.phone_number_is_private = request.form.get('phone_number_is_private') == 'true'
    user.address = address
    user.address_is_private = request.form.get('address_is_private') == 'true'

    try:
        user.birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Érvénytelen születési idő formátum!'
        }), 400

    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user.id}_{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            file.save(filepath)

            attachment = Attachment(
                filename=filename
            )
            db.session.add(attachment)
            db.session.flush()
            user.profile_picture = attachment.id

    enable_2fa = request.form.get('2fa_enabled') == 'true'
    if enable_2fa and not user._2fa_enabled:
        return jsonify({
            'success': False,
            'error': 'A 2FA bekapcsolasahoz elobb sikeres kodellenorzes szukseges.'
        }), 400

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Profil sikeresen frissítve!'
    }), 200

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
    user_items = Item.query.filter_by(uploader_id=user.id, active=True).order_by(Item.created_at.desc()).all()
    current_language = _normalize_language(
        request.cookies.get('lang') or request.headers.get('Accept-Language')
    )
    for item in user_items:
        item.localized_description = _localized_description(item, current_language)

    total = len(user_items)
    lost_count = sum(1 for i in user_items if i.type == 'lost')
    found_count = sum(1 for i in user_items if i.type == 'found')
    return render_template(
        "profile.html",
        user=user,
        items=user_items,
        total=total,
        lost_count=lost_count,
        found_count=found_count,
        profile_picture_path=_get_profile_picture_url(user)
    )


@profile_routes.route('/createprofile', methods=['GET', 'POST'])
@login_required
def createprofile():
    if request.method == 'POST':
        try:
            return _save_profile_form(current_user)
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Hiba a profil frissítésénél: {str(e)}'
            }), 400

    return render_template(
        "createprofile.html",
        user=current_user,
        profile_picture_path=_get_profile_picture_url(current_user)
    )


@profile_routes.route('/editprofile', methods=['GET', 'POST'])
@login_required
def editprofile():
    if request.method == 'POST':
        try:
            return _save_profile_form(current_user)
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Hiba a profil frissítésénél: {str(e)}'
            }), 400

    return render_template(
        "editprofile.html",
        user=current_user,
        profile_picture_path=_get_profile_picture_url(current_user)
    )


@profile_routes.route('/create2fa', methods=['POST'])
@login_required
def create_2fa():
    otp_code = (request.form.get('2fa_code') or '').strip()

    if otp_code:
        _2fa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
        if not _2fa:
            return jsonify({
                'success': False,
                'error': 'Nincs elozetes 2FA beallitas ehhez a felhasznalohoz.'
            }), 400

        if not _2fa.verify_otp(otp_code):
            return jsonify({
                'success': False,
                'error': 'Hibas ellenorzo kod.'
            }), 400

        current_user._2fa_enabled = True
        current_user._2fa_id = _2fa.id
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Ketfaktoros hitelesites engedelyezve.'
        }), 200

    if current_user._2fa_enabled:
        return jsonify({
            'success': False,
            'error': 'A ketfaktoros hitelesites mar engedelyezve van.'
        }), 400

    _2fa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()
    if not _2fa:
        _2fa = TwoFactorAuth(user_id=current_user.id)
        session['2fa_key'] = _2fa.set_2fa_secret()
        db.session.add(_2fa)
        db.session.commit()

    return jsonify({
        'success': True,
        'qr_code': _2fa.generate_qr_code(current_user.email)
    }), 200


@profile_routes.route('/report-user/<int:user_id>', methods=['POST'])
@login_required
def report_user(user_id):
    """Report a user"""
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': 'Bejelentkezés szükséges!'
        }), 401
    
    # Check if user is reporting themselves
    if current_user.id == user_id:
        return jsonify({
            'success': False,
            'error': 'Nem jellentheted magadat!'
        }), 400
    
    # Check if user exists
    reported_user = User.query.get(user_id)
    if not reported_user:
        return jsonify({
            'success': False,
            'error': 'Felhasználó nem található!'
        }), 404
    
    reason = request.form.get('reason', '').strip()
    content = request.form.get('content', '').strip()
    
    if not reason:
        return jsonify({
            'success': False,
            'error': 'Az indoklás megadása kötelező!'
        }), 400
    
    # Check if user already reported this user
    existing_report = Reports.query.filter_by(
        reporter_id=current_user.id,
        user_id=user_id,
        pending=True
    ).first()
    
    if existing_report:
        return jsonify({
            'success': False,
            'error': 'Már bejelentettél ezt a felhasználót!'
        }), 400
    
    # Create report
    report = Reports(
        reporter_id=current_user.id,
        user_id=user_id,
        reason=reason,
        content=content,
        pending=True
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Bejelentés sikeresen elküldve!'
    }), 200