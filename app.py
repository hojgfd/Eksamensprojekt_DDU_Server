from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "data.db")


# INIT DATABASE ()
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Todo lists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todolists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    # Tasks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            todolist_id INTEGER,
            text TEXT,
            completed BOOLEAN DEFAULT 0,
            FOREIGN KEY(todolist_id) REFERENCES todolists(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------------
# HJÆLPE-FUNKTIONER
# -------------------------
def get_todolist_id(name):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM todolists WHERE name=?", (name,))
    row = cursor.fetchone()
    if row:
        todolist_id = row[0]
    else:
        # Opret ny liste hvis den ikke findes
        cursor.execute("INSERT INTO todolists (name) VALUES (?)", (name,))
        todolist_id = cursor.lastrowid
        conn.commit()
    conn.close()
    return todolist_id

def get_tasks(list_name):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM todolists WHERE name=?", (list_name,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return []
    todolist_id = row[0]
    cursor.execute("SELECT id, text, completed FROM tasks WHERE todolist_id=?", (todolist_id,))
    todos = [{"id": tid, "text": text, "completed": completed} for tid, text, completed in cursor.fetchall()]
    conn.close()
    return todos

# -------------------------
# ROUTES
# -------------------------
# Forside
@app.route('/')
def home():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM todolists")
    lists = [row[0] for row in cursor.fetchall()]
    conn.close()
    return render_template('home.html', lists=lists)

# Dynamisk liste
@app.route('/<list_name>')
def show_list(list_name):
    todos = get_tasks(list_name)
    return render_template('list.html', todos=todos, list_name=list_name)

# Tilføj todo
@app.route('/add-todo', methods=['POST'])
def add_todo():
    list_name = request.form.get('list_name').strip()
    text = request.form.get('text').strip()
    if not list_name or not text:
        return redirect(url_for('home'))

    todolist_id = get_todolist_id(list_name)
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (todolist_id, text, completed) VALUES (?, ?, ?)",
                   (todolist_id, text, 0))
    conn.commit()
    conn.close()
    return redirect(url_for('show_list', list_name=list_name))

# Slet todo
@app.route('/delete-todo/<list_name>/<int:task_id>', methods=['POST'])
def delete_todo(list_name, task_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

# Toggle completed
@app.route('/toggle-todo/<list_name>/<int:task_id>', methods=['POST'])
def toggle_todo(list_name, task_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT completed FROM tasks WHERE id=?", (task_id,))
    row = cursor.fetchone()
    if row:
        new_status = 0 if row[0] else 1
        cursor.execute("UPDATE tasks SET completed=? WHERE id=?", (new_status, task_id))
        conn.commit()
    conn.close()
    return jsonify({"status": "toggled"})

if __name__ == '__main__':
    app.run(debug=True)
