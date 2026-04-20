from flask import *
from datetime import datetime, timedelta
import sqlite3
from database import get_db
from routes.auth_api import token_required

focusmode_api = Blueprint("focusmode_api", __name__)


@focusmode_api.route('/api/focus-session', methods=['POST'])
@token_required
def api_add_focus_session():
    data = request.get_json(silent=True) or {}

    minutes = data.get("minutes")
    distractions = data.get("distractions", 0)
    session_date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    user_id = g.user_id

    try:
        minutes = int(minutes)
        distractions = int(distractions)
    except (TypeError, ValueError):
        return jsonify({"error": "minutes og distractions skal være tal"}), 400

    if minutes < 0 or distractions < 0:
        return jsonify({"error": "værdier må ikke være negative"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO focus_sessions (session_date, minutes, distractions, created_at, user_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session_date,
        minutes,
        distractions,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_id,
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"}), 201


@focusmode_api.route('/api/focus-data', methods=['GET'])
@token_required
def api_focus_data():
    conn = get_db()
    cursor = conn.cursor()
    user_id = g.user_id

    cursor.execute("""
        SELECT 
            session_date AS date,
            SUM(minutes) AS total_minutes,
            SUM(distractions) AS total_distractions
        FROM focus_sessions 
        WHERE user_id = ?
        GROUP BY session_date
        ORDER BY session_date
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "date": row[0],
            "minutes": row[1],
            "distractions": row[2]
        }
        for row in rows
    ])
