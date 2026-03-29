from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from database import db, User, Item, Attachment, Category
from werkzeug.utils import secure_filename, send_from_directory
import os
import uuid

post_routes = Blueprint("post", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@post_routes.route('/post/create', methods=['POST'])
@login_required
def create_post():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
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
        description=description,
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

    return jsonify({'success': True, 'item_id': item.id})


@post_routes.route('/post', defaults={'item_id': 1})
@post_routes.route('/post/<int:item_id>')
def post(item_id):
    item = Item.query.get(item_id)
    if item is None:
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

