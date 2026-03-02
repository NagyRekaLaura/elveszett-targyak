from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user
from database import db, User, Item
main_routes = Blueprint("main", __name__)

@main_routes.route('/')
def home():
    items = Item.query.filter_by(active=True).all()
    return render_template("home.html", items=items)
    