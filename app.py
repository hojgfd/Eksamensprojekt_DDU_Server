from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Forside med dropdown
@app.route('/')
def home():
    lists = ["list1", "list2", "list3", "Work"]
    return render_template('home.html', lists=lists)

# Routes for hver liste
@app.route('/list1')
def list1():
    # 'todos' sendes som eksempel, backend håndterer rigtige data
    todos = [
        {"text": "Eksempel opgave 1", "completed": 0, "source": "user"},
        {"text": "Eksempel opgave 2", "completed": 1, "source": "friend"}
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
    # Her antages backend håndterer data, vi redirecter kun til korrekt liste
    list_name = request.form.get('list_name')
    if list_name.lower() == "work":
        return redirect(url_for('work_list'))
    else:
        return redirect(url_for(list_name.lower()))

if __name__ == '__main__':
    app.run(debug=True)
