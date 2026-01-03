from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date

app = Flask(__name__)

# ---------- DATABASE CONNECTION ----------
def get_db():
    return sqlite3.connect("database.db")

# ---------- CREATE TABLES ----------
with get_db() as db:
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        date TEXT,
        status TEXT
    )
    """)

    cursor.execute("""
CREATE TABLE IF NOT EXISTS leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    reason TEXT,
    status TEXT
)
""")
    cursor.execute("""
CREATE TABLE IF NOT EXISTS payroll (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    month TEXT,
    salary INTEGER
)
""")



# ---------- ROUTES ----------
@app.route('/')
def home():
    return redirect('/login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        with get_db() as db:
            db.execute(
                "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                (email, password, role)
            )

        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_db().execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        if user:
            if user[3] == 'admin':
                return redirect('/admin')
            else:
                return redirect(url_for('employee_dashboard', email=email))

        return "Invalid Login"

    return render_template('login.html')


@app.route('/employee/<email>')
def employee_dashboard(email):
    return render_template('employee_dashboard.html', email=email)

@app.route('/profile/<email>')
def profile(email):
    user = get_db().execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    ).fetchone()
    return render_template('profile.html', user=user)


@app.route('/mark_attendance/<email>', methods=['GET', 'POST'])
def mark_attendance(email):
    if request.method == 'POST':
        with get_db() as db:
            db.execute(
                "INSERT INTO attendance (user_email, date, status) VALUES (?, ?, ?)",
                (email, str(date.today()), "Present")
            )
        return redirect(f'/employee/{email}')

    return render_template('attendance_confirm.html', email=email)



@app.route('/admin')
def admin_dashboard():
    records = get_db().execute("SELECT * FROM attendance").fetchall()
    return render_template('admin_dashboard.html', records=records)

@app.route('/payroll/<email>')
def payroll(email):
    salary = get_db().execute(
        "SELECT * FROM payroll WHERE user_email=?",
        (email,)
    ).fetchall()
    return render_template('payroll.html', salary=salary, email=email)



# ---------- LEAVE APPLY ----------
@app.route('/apply_leave/<email>', methods=['GET', 'POST'])
def apply_leave(email):
    if request.method == 'POST':
        reason = request.form['reason']

        with get_db() as db:
            db.execute(
                "INSERT INTO leaves (user_email, reason, status) VALUES (?, ?, ?)",
                (email, reason, "Pending")
            )

        return redirect(f'/employee/{email}')

    return render_template('apply_leave.html', email=email)

@app.route('/my_leaves/<email>')
def my_leaves(email):
    leaves = get_db().execute(
        "SELECT * FROM leaves WHERE user_email=?",
        (email,)
    ).fetchall()
    return render_template('my_leaves.html', leaves=leaves, email=email)

@app.route('/logout')
def logout():
    return redirect('/login')


@app.route('/employees')
def employees():
    users = get_db().execute(
        "SELECT * FROM users WHERE role='employee'"
    ).fetchall()
    return render_template('employees.html', users=users)

# ---------- ADMIN VIEW LEAVES ----------
@app.route('/view_leaves')
def view_leaves():
    leaves = get_db().execute("SELECT * FROM leaves").fetchall()
    return render_template('leaves.html', leaves=leaves)


# ---------- APPROVE LEAVE ----------
@app.route('/approve_leave/<int:leave_id>')
def approve_leave(leave_id):
    with get_db() as db:
        db.execute(
            "UPDATE leaves SET status='Approved' WHERE id=?",
            (leave_id,)
        )
        db.commit()
    return redirect('/view_leaves')

with get_db() as db:
    db.execute(
        "INSERT INTO payroll (user_email, month, salary) VALUES (?, ?, ?)",
        ("hetavihdesai007@gmail.com", "April 2024", 30000)
    )
@app.route('/add_payroll', methods=['GET', 'POST'])
def add_payroll():
    if request.method == 'POST':
        email = request.form['email']
        month = request.form['month']
        salary = request.form['salary']

        with get_db() as db:
            db.execute(
                "INSERT INTO payroll (user_email, month, salary) VALUES (?, ?, ?)",
                (email, month, salary)
            )

        return redirect('/admin')

    return render_template('add_payroll.html')

@app.route('/delete_payroll/<int:id>')
def delete_payroll(id):
    with get_db() as db:
        db.execute("DELETE FROM payroll WHERE id=?", (id,))
    return redirect('/admin')


@app.route('/edit_payroll/<int:id>', methods=['GET', 'POST'])
def edit_payroll(id):
    db = get_db()
    payroll = db.execute(
        "SELECT * FROM payroll WHERE id=?", (id,)
    ).fetchone()

    if request.method == 'POST':
        salary = request.form['salary']
        db.execute(
            "UPDATE payroll SET salary=? WHERE id=?",
            (salary, id)
        )
        db.commit()
        return redirect('/admin')

    return render_template('edit_payroll.html', payroll=payroll)
@app.route('/attendance_chart/<email>')
def attendance_chart(email):
    data = get_db().execute(
        "SELECT date FROM attendance WHERE user_email=?",
        (email,)
    ).fetchall()

    dates = [d[0] for d in data]
    counts = list(range(1, len(dates) + 1))

    return render_template(
        'chart.html',
        dates=dates,
        counts=counts,
        email=email
    )
@app.route('/clear_payroll')
def clear_payroll():
    with get_db() as db:
        db.execute("DELETE FROM payroll")
    return "Payroll cleared"
@app.route('/search', methods=['GET', 'POST'])
def search():
    result = None
    if request.method == 'POST':
        keyword = request.form['keyword']
        db = get_db()
        result = db.execute(
            "SELECT * FROM users WHERE name LIKE ? OR email LIKE ?",
            (f"%{keyword}%", f"%{keyword}%")
        ).fetchall()

    return render_template('search.html', result=result)

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)

