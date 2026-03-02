from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required, login_user, logout_user
from database import db, User

auth_routes = Blueprint("auth", __name__)

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action_type = request.form.get("type")

        if action_type == "login":
            username = request.form.get("username")
            password = request.form.get("passwd")

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user, remember=True)
                return redirect(url_for("main.home"))

        elif action_type == "register":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("passwd")

            if User.query.filter_by(username=username).first():
                return render_template("login.html", error="Felhasznalonev foglalt")

            if User.query.filter_by(email=email).first():
                return render_template("login.html", error="Email foglalt")

            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)

            return redirect(url_for("main.home"))

    return render_template("login.html")

@auth_routes.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))



        
    