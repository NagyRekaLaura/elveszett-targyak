from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, current_app
from flask_login import login_user
from sqlalchemy import or_
from database import db, User, Item, Attachment, Category
main_routes = Blueprint("main", __name__)


def _normalize_language(language_value):
    language_value = (language_value or '').strip().lower()
    return 'en' if language_value.startswith('en') else 'hu'


def _localized_description(item, language):
    if language == 'en':
        return item.description_en or item.description_hu or ''
    return item.description_hu or item.description_en or ''

@main_routes.route('/')
def home():
    search_query = (request.args.get('q') or '').strip()
    query = Item.query.filter_by(active=True, is_closed=False)

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.outerjoin(Category, Item.category_id == Category.id).filter(
            or_(
                Item.name.ilike(like_pattern),
                Item.description_hu.ilike(like_pattern),
                Item.description_en.ilike(like_pattern),
                Item.type.ilike(like_pattern),
                Item.location.ilike(like_pattern),
                Category.name.ilike(like_pattern),
            )
        )

    items = query.order_by(Item.created_at.desc()).all()
    current_language = _normalize_language(
        request.cookies.get('lang') or request.headers.get('Accept-Language')
    )
    for item in items:
        item.localized_description = _localized_description(item, current_language)

    # Feltöltők lekérése
    uploader_ids = {item.uploader_id for item in items}
    uploaders = {u.id: u for u in User.query.filter(User.id.in_(uploader_ids)).all()} if uploader_ids else {}
    return render_template("home.html", items=items, uploaders=uploaders, at=Attachment, search_query=search_query)

@main_routes.route('/varmegyek.json')
def varmegyek():
    
    return send_from_directory(current_app.root_path, 'varmegyek.json')
