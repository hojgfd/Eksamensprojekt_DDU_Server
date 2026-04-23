#HELE FIL FRA https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/auth.py
from flask import Blueprint, render_template, request, redirect, session, url_for
from models import create_user, get_user, get_user_by_email, update_password
from werkzeug.security import check_password_hash
import random
import string
from datetime import datetime, timedelta
from models import get_db
import smtplib
from email.mime.text import MIMEText
from tokens import *


auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        email = request.form.get("email","").strip()
        password = request.form.get("password","").strip()

        if not username or not email or not password:
            return render_template("register.html", error="Udfyld alle felter")

        if get_user(username) or get_user_by_email(email):
            return render_template(
                "register.html",
                error="Brugernavn/email findes allerede"
            )

        user_id = create_user(username, email, password)

        return render_template("login.html", error="Tjek din email for at aktivere din konto")

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()

        if not username or not password:
            return render_template("login.html", error="Udfyld alle felter")

        user = get_user(username)

        if not user:
            return render_template("login.html", error="Username does not exist")

        if user and check_password_hash(user["password"], password):
            token = create_token(user["id"]) #burde kigge på
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "token": token
            }
            session["token"] = token
            return redirect("/")


    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email","").strip()
        session["reset_email"] = email
        session["resend_available_at"] = (datetime.now() + timedelta(seconds=20)).timestamp()

        user = get_user_by_email(email)
        if not user:
            return render_template("forgot_password.html", error="Email findes ikke")

        code = ''.join(random.choices(string.digits, k=6))
        expires = datetime.now() + timedelta(minutes=10)

        db = get_db()
        db.execute(
            "INSERT INTO password_resets (user_id, code, expires_at) VALUES (?, ?, ?)",
            (user["id"], code, expires.strftime("%Y-%m-%d %H:%M:%S"))
        )
        db.commit()
        db.close()

        # SEND MAIL
        send_email(email, code)

        return redirect(url_for("auth.verify_code"))

    return render_template("forgot_password.html")

@auth.route("/verify-code", methods=["GET", "POST"])
def verify_code():
    if request.method == "POST":

        email = session.get("reset_email")
        code = request.form.get("code","").strip()

        if not code:
            return render_template("verify_code.html", error="Udfyld felt")

        user = get_user_by_email(email)
        if not user:
            return render_template("verify_code.html", error="Fejl i email")

        db = get_db()

        reset = db.execute(
            "SELECT * FROM password_resets WHERE user_id=? AND code=?",
            (user["id"], code)
        ).fetchone()

        db.close()

        if not reset:
            return render_template("verify_code.html", error="Forkert kode")

        session["reset_user_id"] = user["id"]
        return redirect(url_for("auth.reset_password"))

    return render_template("verify_code.html")



@auth.route("/reset-password/", methods=["GET", "POST"])
def reset_password():
    user_id = session.get("reset_user_id")

    if not user_id:
        return redirect("/login")

    if request.method == "POST":
        password = request.form.get("password","").strip()
        confirm = request.form.get("confirm","").strip()

        if password != confirm:
            return render_template("reset_password.html", error="Passwords matcher ikke")

        update_password(user_id, password)

        session.pop("reset_user_id",None)

        return redirect("/login")

    return render_template("reset_password.html")

def send_email(to_email, code):
    import smtplib
    from email.mime.text import MIMEText

    sender_email = "dduprojekt@gmail.com"
    sender_password = "yerg znme rlnw afiu"

    msg = MIMEText(f"""
Din recovery kode er: {code}

Koden udløber om 10 minutter.
""")

    msg["Subject"] = "DDU Projekt - Password reset"
    msg["From"] = f"DDU Projekt <{sender_email}>"
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(sender_email, sender_password)

    server.sendmail(sender_email, to_email, msg.as_string())

    server.quit()

@auth.route("/resend-code", methods=["POST"])
def resend_code():
    email = session.get("reset_email")

    user = get_user_by_email(email)
    if not user:
        return render_template("verify_code.html", error="Email findes ikke")

    # cooldown check
    available_at = session.get("resend_available_at", 0)
    now = datetime.now().timestamp()

    if now < available_at:
        return render_template("verify_code.html", error="Vent før du kan sende igen")


    code = ''.join(random.choices(string.digits, k=6))
    expires = datetime.now() + timedelta(minutes=10)

    db = get_db()
    db.execute(
        "INSERT INTO password_resets (user_id, code, expires_at) VALUES (?, ?, ?)",
        (user["id"], code, expires.strftime("%Y-%m-%d %H:%M:%S"))
    )
    db.commit()
    db.close()

    send_email(email, code)

    # reset cooldown ()
    session["resend_available_at"] = (datetime.now() + timedelta(seconds=20)).timestamp()

    return render_template("verify_code.html", error="Ny kode sendt")
