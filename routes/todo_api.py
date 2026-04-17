from flask import *
import sqlite3
from database import get_db
from routes.auth_api import token_required

todo_api = Blueprint("todo_api", __name__)

# Opret en ny todo-liste
@todo_api.route('/api/todolists', methods=['POST'])
@token_required
def api_create_todolist():
    conn = get_db()
    cursor = conn.cursor()
    data = request.json
    name = data.get("name")
    user_id = g.user_id
    if not name:
        return jsonify({"error": "name is required"}), 400
    try:
        cursor.execute("INSERT INTO todolists (name, user_id) VALUES (?, ?)", (name, user_id))
        conn.commit()
        todolist_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Todo list already exists"}), 409
    conn.close()

    return jsonify({"id": todolist_id, "name": name}), 201

# Slet en todo-liste
@todo_api.route('/api/todolists/<int:list_id>', methods=['DELETE'])
@token_required
def api_delete_todolist(list_id):
    conn = get_db()
    cursor = conn.cursor()

    # Check ownership
    cursor.execute(
        "SELECT id FROM todolists WHERE id=? AND user_id=?",
        (list_id, g.user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    # Delete tasks first
    cursor.execute("DELETE FROM tasks WHERE todolist_id=?", (list_id,))
    cursor.execute("DELETE FROM todolists WHERE id=?", (list_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})

# Hent tasks for en liste
@todo_api.route('/api/todolists/<int:list_id>/tasks', methods=['GET'])
@token_required
def api_get_tasks(list_id):
    conn = get_db()
    cursor = conn.cursor()

    # Check ownership
    cursor.execute(
        "SELECT id FROM todolists WHERE id=? AND user_id=?",
        (list_id, g.user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    cursor.execute(
        "SELECT id, text, completed FROM tasks WHERE todolist_id=?",
        (list_id,)
    )
    tasks = [
        {"id": tid, "text": text, "completed": bool(completed)}
        for tid, text, completed in cursor.fetchall()
    ]

    conn.close()
    return jsonify(tasks)

# Tilføj task til en liste
@todo_api.route('/api/todolists/<int:list_id>/tasks', methods=['POST'])
@token_required
def api_add_task(list_id):
    conn = get_db()
    cursor = conn.cursor()

    # Check ownership
    cursor.execute(
        "SELECT id FROM todolists WHERE id=? AND user_id=?",
        (list_id, g.user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    text = data.get("text")

    if not text:
        conn.close()
        return jsonify({"error": "text is required"}), 400

    cursor.execute(
        "INSERT INTO tasks (todolist_id, text, completed) VALUES (?, ?, ?)",
        (list_id, text, 0)
    )
    conn.commit()

    task_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "id": task_id,
        "text": text,
        "completed": False,
        "todolist_id": list_id
    }), 201



# Opdater en task (fx markér som completed)
@todo_api.route('/api/tasks/<int:task_id>', methods=['PATCH'])
@token_required
def api_update_task(task_id):
    conn = get_db()
    cursor = conn.cursor()
    data = request.json

    # Check ownership
    cursor.execute("""
        SELECT tasks.id
        FROM tasks
        JOIN todolists ON tasks.todolist_id = todolists.id
        WHERE tasks.id=? AND todolists.user_id=?
    """, (task_id, g.user_id))

    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    if "completed" in data:
        cursor.execute(
            "UPDATE tasks SET completed=? WHERE id=?",
            (int(data["completed"]), task_id)
        )

    if "text" in data:
        cursor.execute(
            "UPDATE tasks SET text=? WHERE id=?",
            (data["text"], task_id)
        )

    conn.commit()

    cursor.execute(
        "SELECT id, todolist_id, text, completed FROM tasks WHERE id=?",
        (task_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        tid, todolist_id, text, completed = row
        return jsonify({
            "id": tid,
            "todolist_id": todolist_id,
            "text": text,
            "completed": bool(completed)
        })
    else:
        return jsonify({"error": "Task not found"}), 404

# Slet en task
@todo_api.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def api_delete_task(task_id):
    conn = get_db()
    cursor = conn.cursor()

    # Check ownership
    cursor.execute("""
        SELECT tasks.id
        FROM tasks
        JOIN todolists ON tasks.todolist_id = todolists.id
        WHERE tasks.id=? AND todolists.user_id=?
    """, (task_id, g.user_id))

    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})
