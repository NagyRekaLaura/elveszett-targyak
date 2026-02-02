from flask import Flask
from flask_login import LoginManager
from database import init_db, db, User
from routes import create_routes
import os


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


if __name__ == '__main__':
    app.run(debug=True)#debug=True fejlesztes idejere