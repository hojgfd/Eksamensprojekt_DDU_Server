from flask import Blueprint, request, jsonify, session

from tokens import *
from database import get_db
from werkzeug.security import check_password_hash

auth_api = Blueprint("auth_api", __name__)


@auth_api.route('/api/login', methods=['POST'])
def api_login():
    conn = get_db()
    data = request.json


    username = data.get("username")
    password = data.get("password")


    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()

    conn.close()

    print("INPUT:", username, password)
    print("DB ROW:", row)
    print("HASH MATCH:", check_password_hash(row[1], password) if row else None)

    # user not found OR password mismatch
    if not row or not check_password_hash(row[1], password):
        return jsonify({"error": "Invalid"}), 401

    token = create_token(row[0])

    session["token"] = token

    return jsonify({"token": token})