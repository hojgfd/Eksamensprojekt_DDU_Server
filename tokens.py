import jwt
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta

JWT_SECRET = ("JWT_SECRET")
JWT_ALGO = "HS256"

# Create token
def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

# Verify token decorator
def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401

        token = auth_header.split(" ")[1]

        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            g.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return wrapper