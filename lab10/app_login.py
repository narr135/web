import os
import re
import csv
import hashlib
from flask import (
    Flask, request, render_template,
    redirect, url_for, session, flash
)

app = Flask(__name__)
app.secret_key = 'example'


EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.csv')
CSV_FIELDS = ['name', 'email', 'age', 'password_hash']


def _ensure_csv():
    """Create users.csv with a header if it doesn't exist yet."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()


def read_users():
    """Return list of dicts (each a user row)."""
    _ensure_csv()
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def find_user_by_email(email):
    """Case-insensitive lookup. Returns dict or None."""
    email = email.strip().lower()
    for user in read_users():
        if user.get('email', '').lower() == email:
            return user
    return None


def add_user(name, email, age, password):
    """Append one user. Returns False if email already exists."""
    if find_user_by_email(email):
        return False
    pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    _ensure_csv()
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow({
            'name':          name.strip(),
            'email':         email.strip().lower(),
            'age':           str(age),
            'password_hash': pw_hash,
        })
    return True


def check_password(email, password):
    """Return the user dict if credentials match, else None."""
    user = find_user_by_email(email)
    if not user:
        return None
    pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return user if user['password_hash'] == pw_hash else None


def validate_registration(form):
    """
    Returns (errors_list, cleaned_data_dict, password_value).
    Validates every field independently and collects ALL errors.
    """
    data = {
        'name':  form.get('name', '').strip(),
        'email': form.get('email', '').strip(),
        'age':   form.get('age', '').strip(),
    }
    password = form.get('password', '')
    password_confirm = form.get('password_confirm', '')

    errors = []


    if not data['name']:
        errors.append('Name is required!')


    if not data['email']:
        errors.append('Invalid email!')
    elif not EMAIL_RE.match(data['email']):
        errors.append('Invalid email!')


    if not data['age']:
        errors.append('Age is required!')
    else:
        try:
            age_int = int(data['age'])
        except ValueError:
            errors.append('Age must be a number!')
        else:
            if not (18 <= age_int <= 100):
                errors.append('Age must be between 18 and 100!')


    if 'password' in form:
        if not password:
            errors.append('Password is required!')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters!')
        elif password != password_confirm:
            errors.append('Passwords do not match!')

    return errors, data, password


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/task1', methods=['GET', 'POST'])
def task1():
    message, success, name = None, False, ''
    if request.method == 'POST':
        name = request.form.get('student', '').strip()
        if not name:
            message = 'Name is required!'
        else:
            message = f'Welcome, {name}!'
            success = True
    return render_template('task1.html',
                           message=message, success=success, name=name)


@app.route('/task2', methods=['GET', 'POST'])
def task2():
    result, success, email = None, False, ''
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            result = 'Invalid email!'
        elif EMAIL_RE.match(email):
            result = 'Valid email!'
            success = True
        else:
            result = 'Invalid email!'
    return render_template('task2.html',
                           result=result, success=success, email=email)


@app.route('/task3', methods=['GET', 'POST'])
def task3():
    result, success, age = None, False, ''
    if request.method == 'POST':
        age = request.form.get('age', '').strip()
        if not age:
            result = 'Age is required!'
        else:
            try:
                age_int = int(age)
            except ValueError:
                result = 'Age must be a number!'
            else:
                if 18 <= age_int <= 100:
                    result = 'Valid age!'
                    success = True
                else:
                    result = 'Age must be between 18 and 100!'
    return render_template('task3.html',
                           result=result, success=success, age=age)


@app.route('/task4', methods=['GET', 'POST'])
def task4():
    errors, success = [], False
    data = {'name': '', 'email': '', 'age': ''}

    if request.method == 'POST':
        errors, data, password = validate_registration(request.form)

        if data['email'] and EMAIL_RE.match(data['email']) \
                and find_user_by_email(data['email']):
            errors.append('Email is already registered!')

        if not errors:
            add_user(data['name'], data['email'], data['age'], password)
            success = True

            session['user_email'] = data['email'].lower()
            session['user_name'] = data['name']
            return redirect(url_for('dashboard'))

    return render_template('task4.html',
                           errors=errors, success=success, data=data)


@app.route('/task5', methods=['GET', 'POST'])
def task5():
    errors, success = [], False
    data = {'name': '', 'email': '', 'age': ''}

    if request.method == 'POST':
        errors, data, _ = validate_registration(request.form)
        if not errors:
            success = True

    return render_template('task5.html',
                           errors=errors, success=success, data=data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    email = ''

    if session.get('user_email') and request.method == 'GET':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            error = 'Email and password are required!'
        else:
            user = check_password(email, password)
            if user is None:
                error = 'Invalid email or password!'
            else:
                session['user_email'] = user['email']
                session['user_name'] = user['name']
                return redirect(url_for('dashboard'))

    return render_template('login.html', error=error, email=email)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if not session.get('user_email'):
        return redirect(url_for('login'))

    user = find_user_by_email(session['user_email'])
    if user is None:

        session.clear()
        return redirect(url_for('login'))

    safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
    return render_template('dashboard.html', user=safe_user)

if __name__ == '__main__':
    _ensure_csv()
    app.run(debug=True)