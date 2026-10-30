import os
import sqlite3
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "tasks.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("TASK_APP_SECRET", "change-this-secret-key-for-local-development")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'Medium',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


LAYOUT = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} · TaskFlow</title>
<style>
:root{--ink:#172033;--muted:#68738a;--blue:#3157d5;--bg:#f3f6fc;--line:#e4e9f2;--white:#fff;--red:#c93645;--green:#16805d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,Segoe UI,Arial,sans-serif}
a{color:var(--blue);text-decoration:none}
.topbar{background:#17264b;color:white;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}
.brand{font-size:21px;font-weight:800;color:white;letter-spacing:.2px}
.nav{display:flex;gap:15px;align-items:center;flex-wrap:wrap}
.nav a{color:white;font-size:14px}
.wrap{max-width:1000px;margin:28px auto;padding:0 16px}
.card{background:white;border:1px solid var(--line);border-radius:15px;padding:22px;box-shadow:0 6px 24px #23385b0a;margin-bottom:18px}
h1{margin:0 0 8px;font-size:28px}h2{font-size:19px;margin:0 0 15px}
.sub{color:var(--muted);margin:0 0 20px;line-height:1.5}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
label{font-size:13px;font-weight:700;display:block;margin-bottom:6px}
input,textarea,select{width:100%;padding:11px 12px;border:1px solid #cfd7e5;border-radius:8px;font:inherit;background:#fff;color:var(--ink)}
textarea{min-height:80px;resize:vertical}
.field{margin-bottom:14px}
.btn{display:inline-block;border:0;border-radius:8px;padding:10px 14px;background:var(--blue);color:white;font-weight:700;font-size:14px;cursor:pointer}
.btn.secondary{background:#e9eefb;color:#243d91}.btn.danger{background:#ffeaed;color:#a91e2c}.btn.green{background:#e2f6ed;color:#126746}
.actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.flash{padding:11px 13px;border-radius:8px;background:#eaf0ff;margin-bottom:12px;color:#24439a}
.flash.error{background:#ffeaed;color:#a91e2c}.flash.success{background:#e2f6ed;color:#126746}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}
.stat{background:#f7f9ff;border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:120px}
.stat strong{font-size:22px;display:block}.stat span{font-size:12px;color:var(--muted)}
.task{border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:12px;display:flex;gap:14px;justify-content:space-between;align-items:flex-start}
.task h3{margin:0 0 6px;font-size:17px;overflow-wrap:anywhere}
.task p{margin:5px 0;color:var(--muted);white-space:pre-wrap;overflow-wrap:anywhere}
.task.completed h3{text-decoration:line-through;color:var(--muted)}
.badge{display:inline-block;border-radius:20px;padding:4px 8px;font-size:11px;font-weight:800;background:#edf1f8;color:#526078}
.badge.High{background:#ffeaed;color:#a91e2c}.badge.Low{background:#e2f6ed;color:#126746}
.badge.done{background:#e2f6ed;color:#126746}
.task-main{min-width:0;flex:1}.empty{text-align:center;padding:28px;color:var(--muted)}
.auth{max-width:440px;margin:45px auto}
small,.muted{color:var(--muted)}
.inline{display:inline}
@media(max-width:650px){.grid{grid-template-columns:1fr}.task{flex-direction:column}.wrap{margin:18px auto}.card{padding:17px}h1{font-size:24px}}
</style>
</head>
<body>
<header class="topbar">
<a class="brand" href="{{ url_for('index') }}">✓ TaskFlow</a>
<nav class="nav">
{% if session.get('user_id') %}
<a href="{{ url_for('index') }}">My Tasks</a>
<span>Hi, {{ session.get('username') }}</span>
<a href="{{ url_for('logout') }}">Log out</a>
{% else %}
<a href="{{ url_for('login') }}">Log in</a><a href="{{ url_for('register') }}">Register</a>
{% endif %}
</nav>
</header>
<main class="wrap">
{% with messages = get_flashed_messages(with_categories=true) %}
{% for category, message in messages %}
<div class="flash {{ category }}">{{ message }}</div>
{% endfor %}
{% endwith %}
{{ body|safe }}
</main>
</body>
</html>
"""


def page(title, body, **context):
    inner = render_template_string(body, **context)
    return render_template_string(LAYOUT, title=title, body=inner)


AUTH_FORM = r"""
<div class="auth card">
<h1>{{ heading }}</h1>
<p class="sub">{{ subtitle }}</p>
<form method="post">
<div class="field"><label for="username">Username</label><input id="username" name="username" minlength="3" maxlength="40" required autocomplete="username"></div>
<div class="field"><label for="password">Password</label><input id="password" type="password" name="password" minlength="8" required autocomplete="{{ 'new-password' if mode == 'register' else 'current-password' }}"></div>
<button class="btn" type="submit">{{ button }}</button>
</form>
<p class="muted">{{ footer|safe }}</p>
</div>
"""


@app.route("/")
@login_required
def index():
    with get_db() as db:
        tasks = db.execute(
            "SELECT * FROM tasks WHERE user_id=? ORDER BY completed ASC, "
            "CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, "
            "CASE WHEN due_date='' THEN 1 ELSE 0 END, due_date ASC, id DESC",
            (session["user_id"],)
        ).fetchall()
    total = len(tasks)
    done_count = sum(task["completed"] for task in tasks)
    open_count = total - done_count
    body = r"""
<div class="card">
<h1>My Tasks</h1>
<p class="sub">Plan your work, track progress, and keep everything in one place.</p>
<div class="stats">
<div class="stat"><strong>{{ total }}</strong><span>Total tasks</span></div>
<div class="stat"><strong>{{ open_count }}</strong><span>Pending</span></div>
<div class="stat"><strong>{{ done_count }}</strong><span>Completed</span></div>
</div>
</div>
<div class="card">
<h2>Add a new task</h2>
<form action="{{ url_for('create_task') }}" method="post">
<div class="field"><label for="title">Task title *</label><input id="title" name="title" maxlength="120" required placeholder="e.g. Finish DBMS assignment"></div>
<div class="field"><label for="description">Description</label><textarea id="description" name="description" maxlength="1000" placeholder="Optional details"></textarea></div>
<div class="grid">
<div class="field"><label for="due_date">Due date</label><input id="due_date" name="due_date" type="date"></div>
<div class="field"><label for="priority">Priority</label><select id="priority" name="priority"><option>Low</option><option selected>Medium</option><option>High</option></select></div>
</div>
<button class="btn" type="submit">+ Add Task</button>
</form>
</div>
<div class="card">
<h2>Task list</h2>
{% if tasks %}
{% for task in tasks %}
<article class="task {{ 'completed' if task.completed else '' }}">
<div class="task-main">
<h3>{{ task.title }}</h3>
{% if task.description %}<p>{{ task.description }}</p>{% endif %}
<div class="actions">
<span class="badge {{ task.priority }}">{{ task.priority }} priority</span>
{% if task.due_date %}<span class="badge">Due: {{ task.due_date }}</span>{% endif %}
<span class="badge {{ 'done' if task.completed else '' }}">{{ 'Completed' if task.completed else 'Pending' }}</span>
</div>
</div>
<div class="actions">
<form class="inline" method="post" action="{{ url_for('toggle_task', task_id=task.id) }}"><button class="btn green" type="submit">{{ 'Undo' if task.completed else 'Complete' }}</button></form>
<a class="btn secondary" href="{{ url_for('edit_task', task_id=task.id) }}">Edit</a>
<form class="inline" method="post" action="{{ url_for('delete_task', task_id=task.id) }}" onsubmit="return confirm('Delete this task?')"><button class="btn danger" type="submit">Delete</button></form>
</div>
</article>
{% endfor %}
{% else %}
<div class="empty">No tasks yet. Add your first task above.</div>
{% endif %}
</div>
"""
    return page("My Tasks", body, tasks=tasks, total=total, open_count=open_count, done_count=done_count)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(username) > 40:
            flash("Username must be between 3 and 40 characters.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        else:
            try:
                with get_db() as db:
                    db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, generate_password_hash(password))
                    )
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That username is already taken. Choose another.", "error")
    return page("Register", AUTH_FORM, heading="Create account",
                subtitle="Register to keep your tasks private.",
                button="Create account", mode="register",
                footer='Already registered? <a href="' + url_for("login") + '">Log in</a>.')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        flash("Incorrect username or password.", "error")
    return page("Log in", AUTH_FORM, heading="Welcome back",
                subtitle="Log in to manage your tasks.",
                button="Log in", mode="login",
                footer='New here? <a href="' + url_for("register") + '">Create an account</a>.')


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("login"))


@app.route("/task/add", methods=["POST"])
@login_required
def create_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    priority = request.form.get("priority", "Medium")
    if not title:
        flash("Task title is required.", "error")
    elif len(title) > 120 or len(description) > 1000:
        flash("Title or description is too long.", "error")
    else:
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        with get_db() as db:
            db.execute(
                "INSERT INTO tasks (user_id, title, description, due_date, priority) VALUES (?, ?, ?, ?, ?)",
                (session["user_id"], title, description, due_date, priority)
            )
        flash("Task added.", "success")
    return redirect(url_for("index"))


@app.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    with get_db() as db:
        task = db.execute(
            "SELECT * FROM tasks WHERE id=? AND user_id=?",
            (task_id, session["user_id"])
        ).fetchone()
        if task is None:
            abort(404)
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            due_date = request.form.get("due_date", "").strip()
            priority = request.form.get("priority", "Medium")
            if not title or len(title) > 120 or len(description) > 1000:
                flash("Enter a title up to 120 characters and description up to 1000 characters.", "error")
            else:
                if priority not in ("Low", "Medium", "High"):
                    priority = "Medium"
                db.execute(
                    "UPDATE tasks SET title=?, description=?, due_date=?, priority=? WHERE id=? AND user_id=?",
                    (title, description, due_date, priority, task_id, session["user_id"])
                )
                flash("Task updated.", "success")
                return redirect(url_for("index"))
    body = r"""
<div class="card">
<h1>Edit task</h1>
<p class="sub">Update the task details below.</p>
<form method="post">
<div class="field"><label for="title">Task title *</label><input id="title" name="title" value="{{ task.title }}" maxlength="120" required></div>
<div class="field"><label for="description">Description</label><textarea id="description" name="description" maxlength="1000">{{ task.description }}</textarea></div>
<div class="grid">
<div class="field"><label for="due_date">Due date</label><input id="due_date" name="due_date" type="date" value="{{ task.due_date }}"></div>
<div class="field"><label for="priority">Priority</label><select id="priority" name="priority">
<option {% if task.priority == 'Low' %}selected{% endif %}>Low</option>
<option {% if task.priority == 'Medium' %}selected{% endif %}>Medium</option>
<option {% if task.priority == 'High' %}selected{% endif %}>High</option>
</select></div>
</div>
<div class="actions"><button class="btn" type="submit">Save changes</button><a class="btn secondary" href="{{ url_for('index') }}">Cancel</a></div>
</form>
</div>
"""
    return page("Edit Task", body, task=task)


@app.route("/task/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    with get_db() as db:
        task = db.execute(
            "SELECT completed FROM tasks WHERE id=? AND user_id=?",
            (task_id, session["user_id"])
        ).fetchone()
        if task is None:
            abort(404)
        db.execute(
            "UPDATE tasks SET completed=? WHERE id=? AND user_id=?",
            (0 if task["completed"] else 1, task_id, session["user_id"])
        )
    flash("Task status updated.", "success")
    return redirect(url_for("index"))


@app.route("/task/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    with get_db() as db:
        db.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, session["user_id"]))
    flash("Task deleted.", "success")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(error):
    return page("Not found", '<div class="card"><h1>Task not found</h1><p class="sub">It may have been deleted or does not belong to your account.</p><a class="btn" href="/">Back to tasks</a></div>'), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)