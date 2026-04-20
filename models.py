#HELE FIL FRA https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/models.py
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def get_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB = os.path.join(BASE_DIR, "data.db")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def create_user(username, email, password):
    db = get_db()

    hashed_password = generate_password_hash(password)

    db.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, hashed_password)
    )
    db.commit()
    db.close()

def update_password(user_id, new_password):
    db = get_db()
    hashed = generate_password_hash(new_password)

    db.execute(
        "UPDATE users SET password=? WHERE id=?",
        (hashed, user_id)
    )
    db.commit()
    db.close()


def get_user(username):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    db.close()
    return user

def get_user_by_email(email):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    db.close()
    return user
