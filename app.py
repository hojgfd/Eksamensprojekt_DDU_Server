from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "data.db")


# INIT DATABASE
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

    # Heart rate table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heartrate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hr INTEGER,
            timestamp TEXT
        )
    """)

    # Indsæt dummy data hvis tabellen er tom
    #cursor.execute("SELECT COUNT(*) FROM heartrate")
    #if cursor.fetchone()[0] == 0:
     #   dummy_data = [
      #      (72, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
       #     (85, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        #    (90, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
         #   (65, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        #]
        #cursor.executemany("INSERT INTO heartrate (hr, timestamp) VALUES (?, ?)", dummy_data)


    conn.commit()
    conn.close()

init_db()

# -------------------------
# HJÆLPE-FUNKTIONER
# -------------------------
def get_todolist_id(name, create_if_missing=True):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM todolists WHERE name=?", (name,))
    row = cursor.fetchone()
    if row:
        todolist_id = row[0]
    else:
        if create_if_missing:
            cursor.execute("INSERT INTO todolists (name) VALUES (?)", (name,))
            todolist_id = cursor.lastrowid
            conn.commit()
        else:
            todolist_id = None
    conn.close()
    return todolist_id


def get_tasks(list_name):
    todolist_id = get_todolist_id(list_name, create_if_missing=False)
    if not todolist_id:
        return []
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, completed FROM tasks WHERE todolist_id=?", (todolist_id,))
    todos = [{"id": tid, "text": text, "completed": completed} for tid, text, completed in cursor.fetchall()]
    conn.close()
    return todos


# -------------------------
# ROUTES
# -------------------------
# Forside
@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/todo')
def home():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM todolists")
    lists = [row[0] for row in cursor.fetchall()]
    conn.close()
    return render_template('home.html', lists=lists)


@app.route('/todo/<list_name>')
def show_list(list_name):
    # Opret listen hvis den ikke findes
    get_todolist_id(list_name)
    todos = get_tasks(list_name)
    return render_template('list.html', todos=todos, list_name=list_name)


@app.route('/focus')
def focus():
    return render_template('focus.html')


# Tilføj todo
@app.route('/add-todo', methods=['POST'])
def add_todo():
    list_name = request.form.get('list_name').strip()
    print(list_name)
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
# Rename liste
@app.route('/rename-list', methods=['POST'])
def rename_list():
    old_name = request.form.get('old_name').strip()
    new_name = request.form.get('new_name').strip()

    if not old_name or not new_name:
        return redirect(url_for('home'))

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Opdater navnet
    cursor.execute("UPDATE todolists SET name=? WHERE name=?", (new_name, old_name))

    conn.commit()
    conn.close()

    return redirect(url_for('show_list', list_name=new_name))


@app.route('/heartratedata')
def heartratedata():
    return render_template("heartrate.html")

@app.route('/api/heartrate')
def api_heartrate():
    hours = int(request.args.get("hours", 24))

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    time_limit = datetime.now() - timedelta(hours=hours)

    cursor.execute("""
        SELECT hr, timestamp 
        FROM heartrate 
        WHERE timestamp >= ?
        ORDER BY timestamp
    """, (time_limit.strftime("%Y-%m-%d %H:%M:%S"),))

    data = cursor.fetchall()
    conn.close()

    return jsonify([
        {"hr": hr, "time": ts} for hr, ts in data
    ])

@app.route('/api/heartrate', methods=['POST'])
def add_heartrate():
    data = request.json

    hr = data.get("hr")

    if not hr:
        return jsonify({"error": "Missing HR"}), 400

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO heartrate (hr, timestamp) VALUES (?, ?)",
        (hr, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


# Slet liste
@app.route('/delete-list', methods=['POST'])
def delete_list():
    list_name = request.form.get('list_name')

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Find liste id
    cursor.execute("SELECT id FROM todolists WHERE name=?", (list_name,))
    row = cursor.fetchone()

    if row:
        todolist_id = row[0]

        # Slet tasks først (foreign key)
        cursor.execute("DELETE FROM tasks WHERE todolist_id=?", (todolist_id,))

        # Slet selve listen
        cursor.execute("DELETE FROM todolists WHERE id=?", (todolist_id,))

        conn.commit()

    conn.close()

    return jsonify({"status": "deleted"})


if __name__ == '__main__':
    app.run(debug=True)
