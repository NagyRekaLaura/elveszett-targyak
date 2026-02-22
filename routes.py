from flask import Flask, jsonify, request, redirect, url_for, render_template
from database import db, User, Item, Category, Attachment
from flask_login import login_user, logout_user, login_required, current_user



def create_routes(app: Flask):
    @app.route('/')
    def home():
        items = Item.query.filter_by(active=True).all()
        return render_template("home.html", items=items)
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            action_type = request.form.get('type')
            if action_type == 'login':
                username = request.form.get('username')
                password = request.form.get('passwd')
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    login_user(user, remember=True)
                    return redirect(url_for('home'))
                else:
                    return render_template("login.html")
            elif action_type == 'register':
                username = request.form.get('username') 
                email = request.form.get('email') 
                password = request.form.get('passwd') 
                if User.query.filter_by(username=username).first(): 
                    return render_template("login.html", error="Felhasznalonev foglalt") 
                if User.query.filter_by(email=email).first(): 
                    return render_template("login.html", error="email foglalt") 
                new_user = User(username=username, email=email) 
                new_user.set_password(password) 
                db.session.add(new_user) 
                db.session.commit() 
                login_user(new_user, remember=True) 
                return redirect(url_for('home'))
        return render_template("login.html")

    @app.route('/poszt')
    def post():
        return render_template("post.html")
    
    @app.route('/profile')
    def profile():
        return render_template("profile.html")
    @app.route('/createprofile')
    def createprofile():
        return render_template("createprofile.html")
    @app.route('/error404')
    def error404():
        return render_template("error404.html")


        