#HELE FIL FRA https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/auth.py
from flask import Blueprint, render_template, request, redirect, session
from models import create_user, get_user

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        create_user(username, password)
        return redirect("/login")

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = get_user(username)

        if user and user["password"] == password:
            session["user"] = {
                "id": user["id"],
                "username": user["username"]
            }
            return redirect("/")

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/login")