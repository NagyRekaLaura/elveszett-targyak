from flask import Flask
from flask_login import LoginManager
from database import init_db, db, User
from routes import create_routes
import os
from datetime import datetime


#set cdw to file lokacio
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

app = Flask(__name__)

app.config['SECRET_KEY'] = 'ldfivhksndvkjbnsdkjvb876jhv'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True #fejlesztes idejere

db.init_app(app)
init_db(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

create_routes(app)


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))

@app.template_filter('fullTime')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    return value.strftime(format)

@app.template_filter('elapsedTime')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
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
    app.run(debug=True)#debug=True fejlesztes idejere