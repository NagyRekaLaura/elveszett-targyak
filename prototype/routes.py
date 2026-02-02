from flask import Flask, jsonify, request, redirect, url_for, render_template
from database import db, User
from flask_login import login_user, logout_user, login_required, current_user



def create_routes(app: Flask):
    @app.route('/')
    def home():
        return render_template("home.html")
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                return render_template("login.html")
        return render_template("login.html")