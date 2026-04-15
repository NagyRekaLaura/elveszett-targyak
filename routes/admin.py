from flask import Blueprint, render_template
from flask_login import login_required

admin_routes = Blueprint("admin", __name__, url_prefix="/admin")


@admin_routes.route("/")
@admin_routes.route("/dashboard")
@login_required
def dashboard():
    return render_template("admin.html")


@admin_routes.route("/users")
@login_required
def users():
    return render_template("admin.html")


@admin_routes.route("/posts")
@login_required
def posts():
    return render_template("admin.html")
