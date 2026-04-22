from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import os
from datetime import datetime, timedelta


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = "JWT_SECRET"

# -------------------------
# DATABASE
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "data.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# IMPORT BLUEPRINTS (EFTER APP + get_db)
# -------------------------
from auth import auth
from routes.auth_api import auth_api
from routes.todo_api import todo_api
from routes.heartrate_api import heartrate_api
from routes.focusmode_api import focusmode_api
from tokens import token_required


app.register_blueprint(auth)
app.register_blueprint(auth_api)
app.register_blueprint(todo_api)
app.register_blueprint(heartrate_api)
app.register_blueprint(focusmode_api)

# INIT DATABASE
def init_db():
    print(app.url_map)
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Login system (fra https://github.com/hojgfd/Eksamensprojekt-Informatik/blob/main/server/database.py)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS users
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT UNIQUE,
                       email TEXT UNIQUE,
                       password TEXT
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
            user_id INTEGER,
            timestamp TEXT
        )
    """)

    # Fokus-sessioner
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS focus_sessions
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       session_date TEXT NOT NULL,
                       minutes INTEGER NOT NULL,
                       distractions INTEGER NOT NULL DEFAULT 0,
                       created_at TEXT NOT NULL,
                       user_id INTEGER
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS password_resets
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER,
                       code TEXT,
                       expires_at TEXT,
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   """)



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
    os.system('cd /home/Shekib/mysite && git pull')
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

    token = session["user"]["token"]
    return render_template('focus.html', token=token)

@app.route('/delete-account', methods=['POST'])
def delete_account():
    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]["id"]

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Slet brugerens data først (vigtigt)
    cursor.execute("DELETE FROM tasks WHERE todolist_id IN (SELECT id FROM todolists WHERE user_id=?)", (user_id,))
    cursor.execute("DELETE FROM todolists WHERE user_id=?", (user_id,))
    cursor.execute("DELETE FROM heartrate WHERE user_id=?", (user_id,))
    cursor.execute("DELETE FROM focus_sessions WHERE user_id=?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

    session.clear()

    return redirect("/login")

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
    user = session.get("user")
    token = user["token"] if user else None
    return render_template("heartrate.html", token=token)



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
