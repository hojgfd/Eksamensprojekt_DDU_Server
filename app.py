from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# Forside med dropdown
@app.route('/')
def home():
    lists = ["list1", "list2", "list3", "Work"]
    return render_template('home.html', lists=lists)

# Routes for hver liste
@app.route('/list1')
def list1():
    todos = [
        {"id": 1, "text": "Eksempel opgave 1", "completed": 0,},
        {"id": 2, "text": "Eksempel opgave 2", "completed": 1,}
    ]
    return render_template('list.html', todos=todos, list_name="list1")

@app.route('/list2')
def list2():
    todos = []
    return render_template('list.html', todos=todos, list_name="list2")

@app.route('/list3')
def list3():
    todos = []
    return render_template('list.html', todos=todos, list_name="list3")

@app.route('/work')
def work_list():
    todos = []
    return render_template('list.html', todos=todos, list_name="Work")

# Route til at tilføje todo (frontend form)
@app.route('/add-todo', methods=['POST'])
def add_todo():
    list_name = request.form.get('list_name')
    # Backend håndterer ikke endnu, redirect til korrekt liste
    if list_name.lower() == "work":
        return redirect(url_for('work_list'))
    else:
        return redirect(url_for(list_name.lower()))

# Route til at slette en todo
@app.route('/delete-todo/<int:task_id>', methods=['POST'])
def delete_todo(task_id):
    # Her kan man senere indsætte database kode
    print(f"Todo med id {task_id} slettet (kun frontend)")
    return jsonify({"status": "deleted"})

if __name__ == '__main__':
    app.run(debug=True)
