from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt 
from flask_login import UserMixin
from datetime import datetime
import pyotp
import qrcode
from io import BytesIO
import base64

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    email = db.Column(db.String(80), unique=True, nullable=True)
    profile_picture = db.Column(db.Integer, db.ForeignKey('attachment.id'), nullable=True)
    name = db.Column(db.String(80), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    phone_number_is_private = db.Column(db.Boolean, default=True)
    address = db.Column(db.String(200), nullable=True)
    address_is_private = db.Column(db.Boolean, default=False)
    _2fa_enabled = db.Column(db.Boolean, default=False)
    _2fa_id = db.Column(db.Integer, db.ForeignKey('two_factor_auth.id'), nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)


    def set_password(self, password: str) -> None:
        '''Jelszó hash-elése és tárolása az adatbázisban'''
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        '''Megadott jelszó ellenőrzése a tárolt hash-sel'''
        return bcrypt.check_password_hash(self.password_hash, password)
    



class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(80), nullable=False) 
    description_hu =  db.Column(db.Text, nullable=True)
    description_en = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    attachments= db.relationship('Attachment', backref='item', lazy=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.String(20), default='lost') 
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    category = db.relationship('Category', backref='items', lazy=True)
    is_closed = db.Column(db.Boolean, default=False)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    filename = db.Column(db.String(255), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.now)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(255), nullable=False)


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    seen = db.Column(db.Boolean, default=False)
    attachment_id = db.Column(db.Integer, db.ForeignKey('attachment.id'), nullable=True)


class TwoFactorAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    secret_key = db.Column(db.String(32), nullable=False)

    def set_2fa_secret(self):
        '''Új 2FA secret generálása és tárolása az adatbázisban'''
        self.secret_key = pyotp.random_base32()
        return self.secret_key
    
    def get_totp(self):
        '''TOTP objektum létrehozása a tárolt secret alapján'''
        return pyotp.TOTP(self.secret_key)
    
    def generate_uri(self, user_email: str) -> str:
        '''URI generálása a QR kódhoz'''
        totp = self.get_totp()
        return totp.provisioning_uri(
            name=user_email,
            issuer_name='Lost&Found'
        )
    
    def generate_qr_code(self, user_email: str):
        '''QR kód generálása a provisioning URI alapján és Base64 formátumban visszaadása'''
        provisioning_uri = self.generate_uri(user_email)
        qr = qrcode.QRCode()
        qr.add_data(provisioning_uri)
        qr.make()
        qr_image = qr.make_image()
        
        # QR kód mentése BytesIO-ba
        img_io = BytesIO()
        qr_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        # Base64 enkódolás
        qr_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        return qr_base64
    
    def verify_otp(self, otp_code: str) -> bool:
        '''Megadott OTP kód ellenőrzése a TOTP objektummal (30sec)'''
        try:
            totp = self.get_totp()
            is_valid = totp.verify(otp_code, valid_window=1)
            return is_valid
        except Exception:
            return False
    
class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    used = db.Column(db.Boolean, default=False)

    def create_token(self):
        '''Egyedi token generálása és tárolása az adatbázisban'''
        self.token = pyotp.random_base32(length=64)
        return self.token
    def is_active(self):
        '''Token érvényességének ellenőrzése'''
        return not self.used 
    def mark_as_used(self):
        '''Token használatának jelzése az adatbázisban'''
        self.used = True
        db.session.commit()
    def get_user(self):
        '''Tokenhez tartozó felhasználó lekérése'''
        return User.query.get(self.user_id)
    def reset_password(self, new_password: str):
        '''Felhasználó jelszavának visszaállítása és token használatának jelzése'''
        user = self.get_user()
        if user and self.is_active():
            user.set_password(new_password)
            db.session.commit()
            self.mark_as_used()
            return True
        return False
        
class Reports(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    pending = db.Column(db.Boolean, default=True)


class Punishments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_ban = db.Column(db.Boolean, default=False)
    is_warning = db.Column(db.Boolean, default=False)
    is_suspension = db.Column(db.Boolean, default=False)

def init_db(app):
    with app.app_context():
        db.create_all()