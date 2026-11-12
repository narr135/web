import re
from flask import Flask, request, render_template

app = Flask(__name__)


EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/task1', methods=['GET', 'POST'])
def task1():
    message = None
    success = False
    name = ''
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
    result = None
    success = False
    email = ''
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
    result = None
    success = False
    age = ''
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



def validate_registration(form):
    """
    Returns (errors_list, cleaned_data_dict).
    Validates every field independently and collects ALL errors.
    """
    data = {
        'name':  form.get('name', '').strip(),
        'email': form.get('email', '').strip(),
        'age':   form.get('age', '').strip(),
    }
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

    return errors, data



@app.route('/task4', methods=['GET', 'POST'])
def task4():
    errors = []
    success = False
    data = {'name': '', 'email': '', 'age': ''}

    if request.method == 'POST':
        errors, data = validate_registration(request.form)
        if not errors:
            success = True

    return render_template('task4.html',
                           errors=errors, success=success, data=data)



@app.route('/task5', methods=['GET', 'POST'])
def task5():
    errors = []
    success = False
    data = {'name': '', 'email': '', 'age': ''}

    if request.method == 'POST':
        errors, data = validate_registration(request.form)
        if not errors:
            success = True

    return render_template('task5.html',
                           errors=errors, success=success, data=data)


if __name__ == '__main__':
    app.run(debug=True)