from flask import *
from datetime import datetime, timedelta
import sqlite3
from database import get_db
from routes.auth_api import token_required

heartrate_api = Blueprint("heartrate_api", __name__)

@heartrate_api.route('/api/heartrate')
@token_required
def api_heartrate():
    hours = int(request.args.get("hours", 24))

    conn = get_db()
    cursor = conn.cursor()
    user_id = g.user_id

    time_limit = datetime.now() - timedelta(hours=hours)

    cursor.execute("""
        SELECT hr, timestamp
        FROM heartrate
        WHERE timestamp >= ? AND user_id=?
        ORDER BY timestamp
    """, (time_limit.strftime("%Y-%m-%d %H:%M:%S"), user_id))

    data = cursor.fetchall()
    conn.close()

    return jsonify([
        {"hr": hr, "time": ts} for hr, ts in data
    ])

@heartrate_api.route('/api/heartrate', methods=['POST'])
@token_required
def add_heartrate():
    data = request.json

    hr = data.get("hr")
    user_id = g.user_id
    if not hr:
        return jsonify({"error": "Missing HR"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO heartrate (hr, timestamp, user_id) VALUES (?, ?, ?)",
        (hr, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})