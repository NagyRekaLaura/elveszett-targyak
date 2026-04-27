from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from database import db, User, Item, Attachment, Category, Reports, Punishments
from werkzeug.utils import secure_filename, send_from_directory
import os
import threading
import uuid
from routes.translate import Translate
from datetime import datetime
from sockets.main import notify_user

post_routes = Blueprint("post", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _normalize_language(language_value):
    language_value = (language_value or '').strip().lower()
    return 'en' if language_value.startswith('en') else 'hu'


def _localized_description(item, language):
    if language == 'en':
        return item.description_en or item.description_hu or ''
    return item.description_hu or item.description_en or ''


def _translate_in_background(app, item_id, source_language, source_text):
    try:
        with app.app_context():
            item = Item.query.get(item_id)
            if not item:
                return

            if item.description_hu and item.description_en:
                item.active = True
                db.session.commit()
                return

            target_language = 'en' if source_language == 'hu' else 'hu'

            api_key = app.config.get('OLLAMA_API_KEY')
            if not api_key:
                if target_language == 'hu':
                    item.description_hu = source_text
                else:
                    item.description_en = source_text
                item.active = bool(item.description_hu and item.description_en)
                db.session.commit()
                return
            notify_user(item.uploader_id, 'A posztod fordítása folyamatban van. Ez néhány másodpercet igénybe vehet.', 'Poszt fordítás')
            translator = Translate()
            translator.set_token(api_key)
            translated_text = translator.translate(target_language, source_text)

            if target_language == 'hu':
                item.description_hu = translated_text
            else:
                item.description_en = translated_text

            item.active = bool(item.description_hu and item.description_en)
            db.session.commit()
            notify_user(item.uploader_id, 'A posztod fordítása elkészült és mostantól látható a listában.', 'Poszt fordítás kész')
    except Exception:
        with app.app_context():
            db.session.rollback()
        app.logger.exception('Hiba tortent a hatterforditas kozben. item_id=%s', item_id)
        notify_user(item.uploader_id, 'Hiba történt a posztod fordítása közben. Kérem ellenőrizd a posztodat, és ha szükséges, szerkeszd meg újra.', 'Poszt fordítás hiba')


@post_routes.route('/post/create', methods=['POST'])
@login_required
def create_post():
    # Check if user is suspended
    suspend_punishment = Punishments.query.filter_by(user_id=current_user.id, is_suspension=True).first()
    if suspend_punishment:
        if suspend_punishment.expires_at and suspend_punishment.expires_at > datetime.now():
            return jsonify({
                'success': False,
                'error': 'Fiókod felfüggesztve van. Nem tudsz posztot létrehozni.'
            }), 403
        else:
            # Suspension expired, delete the record
            db.session.delete(suspend_punishment)
            db.session.commit()
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    language = _normalize_language(
        request.form.get('language')
        or request.cookies.get('lang')
        or request.headers.get('Accept-Language')
    )
    category = request.form.get('category', '').strip()
    location = request.form.get('location', '').strip()
    post_type = request.form.get('type', 'lost').strip()

    if not name or not description:
        return jsonify({'success': False, 'error': 'A név és leírás megadása kötelező.'}), 400

    if post_type not in ('lost', 'found'):
        post_type = 'lost'

    # Kategória keresése vagy létrehozása
    category_icons = {
        'allat': 'fa-paw',
        'elektronika': 'fa-laptop',
        'ruhazat': 'fa-tshirt',
        'ekszer': 'fa-gem',
        'dokumentum': 'fa-file-alt',
        'egyeb': 'fa-gift'
    }
    category_obj = Category.query.filter_by(name=category).first()
    if not category_obj and category:
        category_obj = Category(
            name=category,
            icon=category_icons.get(category, 'fa-tag')
        )
        db.session.add(category_obj)
        db.session.flush()
    category_id = category_obj.id if category_obj else None

    item = Item(
        name=name,
        description_hu=description if language == 'hu' else None,
        description_en=description if language == 'en' else None,
        active=False,
        uploader_id=current_user.id,
        type=post_type,
        category_id=category_id,
        location=location
    )
    db.session.add(item)
    db.session.flush()

    # Képek mentése
    upload_dir = os.path.join(current_app.root_path, 'static', 'attachments')
    os.makedirs(upload_dir, exist_ok=True)

    files = request.files.getlist('images')
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)

            attachment = Attachment(
                filename=filename,
                item_id=item.id
            )
            db.session.add(attachment)

    db.session.commit()

    app_obj = current_app._get_current_object()
    translation_worker = threading.Thread(
        target=_translate_in_background,
        args=(app_obj, item.id, language, description),
        daemon=True,
    )
    translation_worker.start()

    return jsonify({
        'success': True,
        'item_id': item.id,
        'processing': True,
        'message': 'A poszt feltoltve. Forditas folyamatban, hamarosan megjelenik.'
    })


@post_routes.route('/post', defaults={'item_id': 1})
@post_routes.route('/post/<int:item_id>')
def post(item_id):
    item = Item.query.get(item_id)
    if item is None or not item.active:
        return redirect(url_for('main.home'))
    
    if item.is_closed and (not current_user.is_authenticated or item.uploader_id != current_user.id):
        return redirect(url_for('main.home'))

    uploader = User.query.get(item.uploader_id)

    category_name = item.category.name if item.category else "-"
    category_i18n_map = {
        'allat': 'animal',
        'elektronika': 'electronics',
        'ruhazat': 'clothing',
        'ekszer': 'jewelry',
        'dokumentum': 'document',
        'egyeb': 'other',
    }
    category_i18n_key = category_i18n_map.get(category_name.lower()) if category_name != "-" else None

    public_phone = None
    if uploader and uploader.phone_number and not uploader.phone_number_is_private:
        public_phone = uploader.phone_number

    public_email = uploader.email if uploader and uploader.email else None
    contact_value = public_phone or public_email or "-"

    sender_name = "Ismeretlen felhasznalo"
    if uploader:
        sender_name = uploader.name or uploader.username

    previous_ads_count = Item.query.filter_by(uploader_id=item.uploader_id).count() if uploader else 0

    return render_template(
        "post.html",
        item=item,
        uploader=uploader,
        category_name=category_name,
        category_i18n_key=category_i18n_key,
        public_phone=public_phone,
        public_email=public_email,
        contact_value=contact_value,
        sender_name=sender_name,
        previous_ads_count=previous_ads_count,
    )


@post_routes.route('/post/test-map')
def test_map():
    items_with_location = Item.query.filter(
        Item.location.isnot(None),
        Item.location != ''
    ).all()

    unique_settlements = {}
    for item in items_with_location:
        raw_location = (item.location or '').strip()
        if not raw_location:
            continue

        location_parts = [part.strip() for part in raw_location.split(',') if part.strip()]
        settlement = location_parts[-1] if location_parts else raw_location
        key = settlement.casefold()

        if key not in unique_settlements:
            unique_settlements[key] = {
                'name': settlement,
                'post_count': 1,
            }
        else:
            unique_settlements[key]['post_count'] += 1

    settlements = sorted(unique_settlements.values(), key=lambda x: x['name'])
    return render_template('test_map.html', settlements=settlements)


@post_routes.route('/post/<int:item_id>/data', methods=['GET'])
@login_required
def get_post_data(item_id):
    """Fetch post data for editing"""
    item = Item.query.get(item_id)
    
    if item is None:
        return jsonify({'success': False, 'error': 'Poszt nem található.'}), 404
    
    if item.uploader_id != current_user.id:
        return jsonify({'success': False, 'error': 'Nincs jogosultsága szerkeszteni ezt a posztot.'}), 403
    
    location_parts = []
    if item.location:
        location_parts = [part.strip() for part in item.location.split(',')]
    
    megye = location_parts[0] if location_parts else ''
    telepules = location_parts[1] if len(location_parts) > 1 else ''
    
    current_language = (request.cookies.get('lang') or request.headers.get('Accept-Language') or 'hu').lower()
    if current_language.startswith('en'):
        current_language = 'en'
    else:
        current_language = 'hu'
    
    description = (item.description_en if current_language == 'en' else item.description_hu) or item.description_hu or item.description_en or ''
    
    return jsonify({
        'success': True,
        'id': item.id,
        'name': item.name,
        'description': description,
        'category': item.category.name if item.category else 'egyeb',
        'type': item.type,
        'megye': megye,
        'telepules': telepules,
        'is_closed': item.is_closed,
        'attachments': [att.filename for att in item.attachments]
    })


@post_routes.route('/post/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_post(item_id):
    """Update an existing post"""
    item = Item.query.get(item_id)
    
    if item is None:
        return jsonify({'success': False, 'error': 'Poszt nem található.'}), 404
    
    if item.uploader_id != current_user.id:
        return jsonify({'success': False, 'error': 'Nincs jogosultsága szerkeszteni ezt a posztot.'}), 403
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    location = request.form.get('location', '').strip()
    post_type = request.form.get('type', 'lost').strip()
    language = _normalize_language(
        request.form.get('language')
        or request.cookies.get('lang')
        or request.headers.get('Accept-Language')
    )
    is_closed = request.form.get('is_closed', 'false').lower() == 'true'
    
    removed_images_str = request.form.get('removed_images', '[]')
    try:
        import json
        removed_images = json.loads(removed_images_str)
    except:
        removed_images = []
    
    if removed_images:
        upload_dir = os.path.join(current_app.root_path, 'static', 'attachments')
        for filename in removed_images:
            attachment = Attachment.query.filter_by(filename=filename, item_id=item_id).first()
            if attachment:
                db.session.delete(attachment)
                filepath = os.path.join(upload_dir, filename)
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        print(f"Error deleting file {filepath}: {e}")
    
    if not name or not description:
        return jsonify({'success': False, 'error': 'A név és leírás megadása kötelező.'}), 400
    
    if post_type not in ('lost', 'found'):
        post_type = 'lost'
    
    item.name = name
    item.type = post_type
    item.location = location
    item.is_closed = is_closed
    
    if language == 'hu':
        item.description_hu = description
        item.description_en = None  # Nullázni a fordításhoz
    else:
        item.description_en = description
        item.description_hu = None  # Nullázni a fordításhoz
    if category:
        category_icons = {
            'allat': 'fa-paw',
            'elektronika': 'fa-laptop',
            'ruhazat': 'fa-tshirt',
            'ekszer': 'fa-gem',
            'dokumentum': 'fa-file-alt',
            'egyeb': 'fa-gift'
        }
        category_obj = Category.query.filter_by(name=category).first()
        if not category_obj:
            category_obj = Category(
                name=category,
                icon=category_icons.get(category, 'fa-tag')
            )
            db.session.add(category_obj)
            db.session.flush()

        item.category_id = category_obj.id
    
    upload_dir = os.path.join(current_app.root_path, 'static', 'attachments')
    os.makedirs(upload_dir, exist_ok=True)
    
    files = request.files.getlist('images')
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            attachment = Attachment(
                filename=filename,
                item_id=item.id
            )
            db.session.add(attachment)
    
    db.session.commit()
    
    app_obj = current_app._get_current_object()
    translation_worker = threading.Thread(
        target=_translate_in_background,
        args=(app_obj, item.id, language, description),
        daemon=True,
    )
    translation_worker.start()
    
    return jsonify({
        'success': True,
        'message': 'Poszt módosítva.'
    })


@post_routes.route('/post/<int:item_id>/close', methods=['POST'])
@login_required
def close_post(item_id):
    """Toggle closed status of a post"""
    item = Item.query.get(item_id)
    
    if item is None:
        return jsonify({'success': False, 'error': 'Poszt nem található.'}), 404
    
    if item.uploader_id != current_user.id:
        return jsonify({'success': False, 'error': 'Nincs jogosultsága lezárni ezt a posztot.'}), 403
    
    item.is_closed = not item.is_closed
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_closed': item.is_closed,
        'message': 'Poszt lezárva.' if item.is_closed else 'Poszt megnyitva.'
    })


@post_routes.route('/post/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_post(item_id):
    """Delete a post"""
    item = Item.query.get(item_id)
    
    if item is None:
        return jsonify({'success': False, 'error': 'Poszt nem található.'}), 404
    
    if item.uploader_id != current_user.id:
        return jsonify({'success': False, 'error': 'Nincs jogosultsága törölni ezt a posztot.'}), 403
    
    for attachment in item.attachments:
        try:
            filepath = os.path.join(current_app.root_path, 'static', 'attachments', attachment.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            current_app.logger.warning(f'Failed to delete file {attachment.filename}: {e}')
        
        db.session.delete(attachment)
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Poszt törölve.'
    })


@post_routes.route('/report-post/<int:item_id>', methods=['POST'])
@login_required
def report_post(item_id):
    """Report a post"""
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': 'Bejelentkezés szükséges!'
        }), 401
    
    # Check if post exists
    item = Item.query.get(item_id)
    if not item:
        return jsonify({
            'success': False,
            'error': 'Poszt nem található!'
        }), 404
    
    # Check if user is reporting their own post
    if item.uploader_id == current_user.id:
        return jsonify({
            'success': False,
            'error': 'Nem jellentheted a saját posztod!'
        }), 400
    
    reason = request.form.get('reason', '').strip()
    content = request.form.get('content', '').strip()
    
    if not reason:
        return jsonify({
            'success': False,
            'error': 'Az indoklás megadása kötelező!'
        }), 400
    
    # Check if user already reported this post
    existing_report = Reports.query.filter_by(
        reporter_id=current_user.id,
        item_id=item_id,
        pending=True
    ).first()
    
    if existing_report:
        return jsonify({
            'success': False,
            'error': 'Már bejelentettél ezt a posztot!'
        }), 400
    
    # Create report
    report = Reports(
        reporter_id=current_user.id,
        item_id=item_id,
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

