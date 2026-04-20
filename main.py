import json

from flask import Flask, url_for, redirect, request
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO, emit, disconnect
from database import init_db, db, User
import os
from datetime import datetime
from routes import auth_routes, main_routes, post_routes, profile_routes, messages_routes, admin_routes, Translate
from sockets import disable_ai, socketio

AI_DISABLED = False
translate_ai = Translate()
#set cdw to file lokacio
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

app = Flask(__name__)
socketio.init_app(app)



app.register_blueprint(auth_routes)
app.register_blueprint(main_routes)
app.register_blueprint(post_routes)
app.register_blueprint(profile_routes)
app.register_blueprint(messages_routes)
app.register_blueprint(admin_routes)
app.config['SECRET_KEY'] = 'ldfivhksndvkjbnsdkjvb876jhv'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True #fejlesztes idejere

db.init_app(app)
init_db(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'



@app.before_request
def check_profile_completion():
    if not current_user.is_authenticated:
        return
    if request.endpoint in ['profile.createprofile', 'profile.create_2fa', 'static', 'auth.login', 'auth.logout', 'main.varmegyek']:
        return
    if not current_user.name or not current_user.address or not current_user.birthdate:
        return redirect(url_for('profile.createprofile'))

@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))

@app.template_filter('fullTime')
def fullTime(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    return value.strftime(format)

@app.template_filter('elapsedTime')
def elapsedTime(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    perc = 60
    ora = 60*60
    nap = 60*60*24 
    honap = 60*60*24*30
    elasped_seconds = (datetime.now() - value).total_seconds() 
    if elasped_seconds < perc: 
        return f"{int(elasped_seconds)} másodperce" 
    elif elasped_seconds < ora: 
        return f"{int(elasped_seconds // perc)} perce" 
    elif elasped_seconds < nap: 
        return f"{int(elasped_seconds // ora)} órája" 
    elif elasped_seconds < honap: 
        return f"{int(elasped_seconds // nap)} napja"
    else:
        return f"{int(elasped_seconds // honap)} hónapja"



if __name__ == '__main__':
    if os.path.exists('tokens.json'):
        with open('tokens.json', 'r') as f:
            tokens = json.load(f)
            if 'ollama_api_key' in tokens and 'mailgun_api_key' in tokens and tokens['ollama_api_key'] and tokens['mailgun_api_key']:
                app.config['OLLAMA_API_KEY'] = tokens['ollama_api_key']
                app.config['MAILGUN_API_KEY'] = tokens['mailgun_api_key']
            else:
                print("Nem találhatók a szükséges API kulcsok a tokens.json fájlban. Kérem, adja meg őket, különben az AI és email funkciók nem fognak működni.")
                app.config['OLLAMA_API_KEY'] = None
                app.config['MAILGUN_API_KEY'] = None
    else:
        print("Nem található a tokens.json fájl. Létrehozás...")
        with open('tokens.json', 'w') as f:
            json.dump({'ollama_api_key': None, 'mailgun_api_key': None}, f)
        print("Kérem, adja meg az API kulcsokat a tokens.json fájlban, különben az AI és email funkciók nem fognak működni.")
        app.config['OLLAMA_API_KEY'] = None
        app.config['MAILGUN_API_KEY'] = None

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)