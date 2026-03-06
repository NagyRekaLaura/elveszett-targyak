from flask import Flask, url_for, redirect, request
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO, emit, disconnect
from database import init_db, db, User
import os
from datetime import datetime
from routes import auth_routes, main_routes, post_routes, profile_routes
from support_chat import SupportAI, ensure_models
import ollama

AI_DISABLED = False

#set cdw to file lokacio
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Support AI
try:
    with open('ai.txt', 'r', encoding='utf-8') as f:
        AI_DOCS = f.read()
    support_ai = SupportAI(AI_DOCS)
except FileNotFoundError:
    support_ai = None
    print("Warning: ai.txt not found, support AI disabled")

app.register_blueprint(auth_routes)
app.register_blueprint(main_routes)
app.register_blueprint(post_routes)
app.register_blueprint(profile_routes)
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
    if request.endpoint in ['profile.createprofile', 'static', 'auth.login', 'auth.logout']:
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

@socketio.on('connect')
def handle_connect():
    print(f'Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected')

@socketio.on('support_message')
def handle_support_message(data):
    if AI_DISABLED:
        
        emit('support_token', {'token': 'AI is currently not available'})
        emit('support_response_end', {'status': 'complete'})
        return
    if not support_ai:
        emit('support_response', {'error': 'AI not available'})
        return
    
    user_message = data.get('message', '').strip()
    if not user_message:
        return
    
    try:
        for token in support_ai.ask(user_message):
            emit('support_token', {'token': token})
        
        emit('support_response_end', {'status': 'complete'})
    except Exception as e:
        print(f"Error in support AI: {str(e)}")
        emit('support_response', {'error': str(e)})

if __name__ == '__main__':
    try:
        ollama.list()
        ensure_models()
    except:
        print("Ollama is not running or not installed. Please start ollama and ensure it's properly set up.")
        AI_DISABLED = True

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)