from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user
from database import db, User, Item, Attachment, Category
messages_routes = Blueprint("messages", __name__)

@messages_routes.route('/messages')
def messages():
    return render_template("messages.html")