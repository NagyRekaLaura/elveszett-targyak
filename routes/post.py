from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user
from database import db, User, Item, Attachment, Category
post_routes = Blueprint("post", __name__)



@post_routes.route('/post', defaults={'item_id': None})
@post_routes.route('/post/<int:item_id>')
def post(item_id):
    item = Item.query.get(item_id)
    if item is None:
        return redirect(url_for('main.home'))
    return render_template("post.html", item=item)
