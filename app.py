from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import os
from datetime import datetime, timedelta
from auth import auth # fra https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/flask_app.py

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = "minmegethemmeligenøgle" # fra https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/flask_app.py
app.register_blueprint(auth) # fra https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/flask_app.py

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "data.db")

def get_db(): #funktion fra https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/database.py
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# INIT DATABASE
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Login system (fra https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/database.py)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS users
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       username
                       TEXT
                       UNIQUE,
                       password
                       TEXT
                   )
                   """)

    #todo lists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todolists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
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

    # Fokus-sessioner
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS focus_sessions
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       session_date
                       TEXT
                       NOT
                       NULL,
                       minutes
                       INTEGER
                       NOT
                       NULL,
                       distractions
                       INTEGER
                       NOT
                       NULL
                       DEFAULT
                       0,
                       created_at
                       TEXT
                       NOT
                       NULL
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
    if "user" not in session:
        return None

    user_id = session["user"]["id"]

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM todolists WHERE name=? AND user_id=?",
        (name, user_id)
    )
    row = cursor.fetchone()

    if row:
        todolist_id = row[0]
    else:
        if create_if_missing:
            cursor.execute(
                "INSERT INTO todolists (name, user_id) VALUES (?, ?)",
                (name, user_id)
            )
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
    if "user" not in session:
        return redirect("/login")
    else:
        return render_template('landing.html')


@app.route('/todo')
def home():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]["id"]

    cursor.execute(
        "SELECT name FROM todolists WHERE user_id=?",
        (user_id,)
    )
    lists = [row[0] for row in cursor.fetchall()]
    conn.close()
    return render_template('home.html', lists=lists)

@app.route('/update_server', methods=["GET", "POST"])
def update():
    os.system('cd /home/shekib/mysite && git pull')
    os.system("touch /var/www/shekib_pythonanywhere_com_wsgi.py")
    return 'Updated and reloaded'

@app.route('/todo/<list_name>')
def show_list(list_name):
    # Opret listen hvis den ikke findes
    get_todolist_id(list_name)
    todos = get_tasks(list_name)
    return render_template('list.html', todos=todos, list_name=list_name)

@app.route('/focus')
def focus():
    if "user" not in session:
        return redirect("/login")
    return render_template('focus.html')

@app.route('/api/focus-session', methods=['POST'])
def api_add_focus_session():
    data = request.get_json(silent=True) or {}

    minutes = data.get("minutes")
    distractions = data.get("distractions", 0)
    session_date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    try:
        minutes = int(minutes)
        distractions = int(distractions)
    except (TypeError, ValueError):
        return jsonify({"error": "minutes og distractions skal være tal"}), 400

    if minutes < 0 or distractions < 0:
        return jsonify({"error": "værdier må ikke være negative"}), 400

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO focus_sessions (session_date, minutes, distractions, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        session_date,
        minutes,
        distractions,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"}), 201


@app.route('/api/focus-data', methods=['GET'])
def api_focus_data():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            session_date AS date,
            SUM(minutes) AS total_minutes,
            SUM(distractions) AS total_distractions
        FROM focus_sessions
        GROUP BY session_date
        ORDER BY session_date
    """)

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

# Hent alle todo-lister
@app.route('/api/todolists', methods=['GET'])
def api_get_todolists():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM todolists")
    lists = [{"id": lid, "name": name} for lid, name in cursor.fetchall()]
    conn.close()
    return jsonify(lists)

# Opret en ny todo-liste
@app.route('/api/todolists', methods=['POST'])
def api_create_todolist():
    data = request.json
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO todolists (name) VALUES (?)", (name,))
        conn.commit()
        todolist_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Todo list already exists"}), 409
    conn.close()

    return jsonify({"id": todolist_id, "name": name}), 201

# Slet en todo-liste
@app.route('/api/todolists/<int:list_id>', methods=['DELETE'])
def api_delete_todolist(list_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    # Slet tasks først (foreign key)
    cursor.execute("DELETE FROM tasks WHERE todolist_id=?", (list_id,))
    # Slet selve listen
    cursor.execute("DELETE FROM todolists WHERE id=?", (list_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

# Hent tasks for en liste
@app.route('/api/todolists/<int:list_id>/tasks', methods=['GET'])
def api_get_tasks(list_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, completed FROM tasks WHERE todolist_id=?", (list_id,))
    tasks = [{"id": tid, "text": text, "completed": bool(completed)}
             for tid, text, completed in cursor.fetchall()]
    conn.close()
    return jsonify(tasks)

# Tilføj task til en liste
@app.route('/api/todolists/<int:list_id>/tasks', methods=['POST'])
def api_add_task(list_id):
    data = request.json
    text = data.get("text")
    if not text:
        return jsonify({"error": "text is required"}), 400

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (todolist_id, text, completed) VALUES (?, ?, ?)",
        (list_id, text, 0)
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": task_id, "text": text, "completed": False, "todolist_id": list_id}), 201

# Opdater en task (fx markér som completed)
@app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
def api_update_task(task_id):
    data = request.json
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    if "completed" in data:
        cursor.execute("UPDATE tasks SET completed=? WHERE id=?", (int(data["completed"]), task_id))
    if "text" in data:
        cursor.execute("UPDATE tasks SET text=? WHERE id=?", (data["text"], task_id))

    conn.commit()
    cursor.execute("SELECT id, todolist_id, text, completed FROM tasks WHERE id=?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        tid, todolist_id, text, completed = row
        return jsonify({"id": tid, "todolist_id": todolist_id, "text": text, "completed": bool(completed)})
    else:
        return jsonify({"error": "Task not found"}), 404

# Slet en task
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

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
