from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime
import json, os

app = Flask(__name__)
app.secret_key = 'crud-tareas-secret-key'

DB_FILE = 'tasks.json'
USERS = {'admin': 'admin123'}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('Debes iniciar sesion primero.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def load_tasks():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def get_next_id(tasks):
    return max((t['id'] for t in tasks), default=0) + 1

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Usuario y contrasena son obligatorios.', 'error')
            return render_template('login.html')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            flash(f'Bienvenido, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contrasena incorrectos.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Sesion cerrada correctamente.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    tasks = load_tasks()
    status_filter = request.args.get('status', 'all')
    if status_filter == 'pending':
        tasks = [t for t in tasks if not t['completed']]
    elif status_filter == 'completed':
        tasks = [t for t in tasks if t['completed']]
    return render_template('index.html', tasks=tasks, filter=status_filter)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date = request.form.get('due_date', '').strip()
        priority = request.form.get('priority', 'media')
        if not title:
            flash('El titulo es obligatorio.', 'error')
            return render_template('create.html')
        if due_date:
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                flash('Formato de fecha invalido.', 'error')
                return render_template('create.html')
        tasks = load_tasks()
        new_task = {
            'id': get_next_id(tasks),
            'title': title,
            'description': description,
            'due_date': due_date,
            'priority': priority,
            'completed': False,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        tasks.append(new_task)
        save_tasks(tasks)
        flash('Tarea creada exitosamente.', 'success')
        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    tasks = load_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        flash('Tarea no encontrada.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date = request.form.get('due_date', '').strip()
        priority = request.form.get('priority', 'media')
        if not title:
            flash('El titulo es obligatorio.', 'error')
            return render_template('edit.html', task=task)
        if due_date:
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                flash('Formato de fecha invalido.', 'error')
                return render_template('edit.html', task=task)
        task['title'] = title
        task['description'] = description
        task['due_date'] = due_date
        task['priority'] = priority
        save_tasks(tasks)
        flash('Tarea actualizada correctamente.', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', task=task)

@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t['id'] != task_id]
    save_tasks(tasks)
    flash('Tarea eliminada.', 'success')
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle(task_id):
    tasks = load_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if task:
        task['completed'] = not task['completed']
        save_tasks(tasks)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    tasks = load_tasks()
    total = len(tasks)
    completed = sum(1 for t in tasks if t['completed'])
    pending = total - completed
    by_priority = {
        'alta': sum(1 for t in tasks if t['priority'] == 'alta'),
        'media': sum(1 for t in tasks if t['priority'] == 'media'),
        'baja': sum(1 for t in tasks if t['priority'] == 'baja'),
    }
    return render_template('dashboard.html', total=total,
                           completed=completed, pending=pending,
                           by_priority=by_priority, tasks=tasks)

if __name__ == '__main__':
    app.run(debug=True)