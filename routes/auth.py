from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from database import PasswordResetToken, db, User, TwoFactorAuth, Punishments
from flask import current_app as app, flash
from routes.send_mail import send_password_reset_email
from datetime import datetime

auth_routes = Blueprint("auth", __name__)

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action_type = request.form.get("type")

        if action_type == "login":
            username = request.form.get("username")
            password = request.form.get("passwd")
            if len(password) > 72:
                flash("A jelszó nem lehet hosszabb 72 karakternél. Kérem, próbáljon meg egy rövidebb jelszót.", "error")
                return render_template("login.html", error="Jelszó túl hosszú")
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                # Check if user is banned
                ban_punishment = Punishments.query.filter_by(user_id=user.id, is_ban=True).first()
                if ban_punishment:
                    flash("Fiókod bannolva van. Nem tudod bejelentkezni.", "error")
                    return render_template("login.html", error="Fiók bannolva")
                
                # Check if user is suspended (show warning but allow login)
                suspend_punishment = Punishments.query.filter_by(user_id=user.id, is_suspension=True).first()
                if suspend_punishment:
                    if suspend_punishment.expires_at and suspend_punishment.expires_at > datetime.now():
                        flash(f"Fiókod felfüggesztve van. Visszaállítás: {suspend_punishment.expires_at.strftime('%Y-%m-%d %H:%M')}", "warning")
                    else:
                        # Suspension expired, delete the record
                        db.session.delete(suspend_punishment)
                        db.session.commit()
                
                # Check for warnings
                warn_punishment = Punishments.query.filter_by(user_id=user.id, is_warning=True).first()
                if warn_punishment and (not warn_punishment.expires_at or warn_punishment.expires_at > datetime.now()):
                    flash(f"Figyelmeztetésed van: {warn_punishment.reason}", "warning")
                
                if user._2fa_enabled:
                    session['2fa_user_id'] = user.id
                    return redirect(url_for("auth.verify_2fa"))
                if user.role == "admin":
                    login_user(user)
                    return redirect(url_for("admin.dashboard"))
                login_user(user, remember=True)
                return redirect(url_for("main.home"))
            else:
                flash("Hibás felhasználónév vagy jelszó. Kérem, próbálja újra.", "error")
                return render_template("login.html", error="Hibás felhasználónév vagy jelszó")

        elif action_type == "register":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("passwd")

            if User.query.filter_by(username=username).first():
                flash("Ez a felhasználónév már foglalt. Kérem, válasszon egy másik felhasználónevet.", "error")
                return render_template("login.html", error="Felhasznalonev foglalt")

            if User.query.filter_by(email=email).first():
                flash("Ez az email cím már használatban van. Kérem, válasszon egy másik email címet.", "error")
                return render_template("login.html", error="Email foglalt")
            if len(password) > 72:
                flash("A jelszó nem lehet hosszabb 72 karakternél. Kérem, válasszon egy rövidebb jelszót.", "error")
                return render_template("login.html", error="Jelszó túl hosszú")

            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)

            return redirect(url_for("main.home"))

    return render_template("login.html")

@auth_routes.route("/2fa-verification", methods=["GET", "POST"])
def verify_2fa():
    if request.method == "POST":
        user_id = session.get('2fa_user_id')
        otp = request.form.get("otp_code")
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for("auth.login"))
        _2fa = TwoFactorAuth.query.get(user._2fa_id)
        if not _2fa:
            return redirect(url_for("auth.login"))
        if _2fa.verify_otp(otp):
            session.pop('2fa_user_id', None)
            if user.role == "admin":
                login_user(user)
                return redirect(url_for("admin.dashboard"))
            login_user(user, remember=True)
            return redirect(url_for("main.home"))
        else:
            return render_template("2fa_verification.html", error=True)
    
    return render_template("2fa_verification.html")

@auth_routes.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token") if request.method == "GET" else request.form.get("token")

    if request.method == "POST":
        if not token:
            return redirect(url_for("auth.login"))
        new_password = request.form.get("new_password")
        if not new_password:
            flash("Kérem, adja meg az új jelszavát!", "error")
            return redirect(url_for("auth.reset_password", token=token))
        reset = PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset or not reset.reset_password(new_password):
            flash("Érvénytelen vagy már használt token. Kérem, próbálja meg újra a jelszó visszaállítási folyamatot.", "error")
            return redirect(url_for("auth.login"))
        flash("Jelszó sikeresen visszaállítva. Most már bejelentkezhet az új jelszavával.", "success")
        return redirect(url_for("auth.login"))

        
    
    if not token:
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)


@auth_routes.route("/reset_password_req", methods=["POST"])
def reset_password_req():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()

    if not username:
        return jsonify(False)
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(False)
    reset_token = PasswordResetToken(user_id=user.id)
    reset_token.create_token()
    db.session.add(reset_token)
    db.session.commit()
    try:
        send_password_reset_email(user.email, reset_token.token)
        exists = True
    except Exception as e:
        app.logger.error(f"Failed to send password reset email: {e}")
        flash("Hiba történt a jelszó visszaállító email küldése közben. Kérem, próbálja meg később.", "error")
        exists = False

    return jsonify(exists)

@auth_routes.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))



        
    