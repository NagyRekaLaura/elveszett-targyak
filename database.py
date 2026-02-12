from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt 
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)
    



class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(80), nullable=False) 
    description =  db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    attachments= db.relationship('Attachment', backref='item', lazy=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.String(20), default='lost') 
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    filename = db.Column(db.String(255), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.now)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(255), nullable=False)

def init_db(app):
    with app.app_context():
        db.create_all()