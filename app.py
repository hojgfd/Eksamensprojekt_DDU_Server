from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from flask import render_template


app = Flask(__name__)
CORS(app)

DB = 'todo.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        completed INTEGER DEFAULT 0,
        source TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# Helper
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(query, args)
    rows = c.fetchall()
    conn.commit()
    conn.close()
    return (rows[0] if rows else None) if one else rows

# Get all todos
@app.route('/todos', methods=['GET'])
def get_todos():
    rows = query_db('SELECT * FROM todos')
    todos = [
        {"id": r[0], "text": r[1], "completed": r[2], "source": r[3]}
        for r in rows
    ]
    return jsonify(todos)

# Add todo
@app.route('/todos', methods=['POST'])
def add_todo():
    data = request.json
    text = data.get('text')
    source = data.get('source', 'web')
    query_db('INSERT INTO todos (text, source) VALUES (?, ?)', (text, source))
    return jsonify({"success": True})

# Complete todo
@app.route('/todos/<int:todo_id>', methods=['PUT'])
def complete_todo(todo_id):
    query_db('UPDATE todos SET completed = 1 WHERE id = ?', (todo_id,))
    return jsonify({"success": True})

# Watch endpoint
@app.route('/watch-data', methods=['POST'])
def watch_data():
    data = request.json
    task = data.get('task')
    query_db('INSERT INTO todos (text, source) VALUES (?, ?)', (task, 'watch'))
    return jsonify({"success": True})

@app.route('/')
def index():
    return render_template('Home.html')


if __name__ == '__main__':
    app.run(debug=True)
