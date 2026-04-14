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

def create_user(username, password):
    db = get_db()

    hashed_password = generate_password_hash(password)

    db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, hashed_password)
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