from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_json import FlaskJSON, JsonError, json_response, as_json
from flask_mysqldb import MySQL
from functools import wraps
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'f783ee40ac0b848f6d9a24be261091cee02229d87e8021ce04264eb3157c22ab0a04542a8064a3952c037a773fe6f73539505da971be575beb7514a5ac14299d'

json = FlaskJSON(app)

# json config
app.config['JSON_ADD_STATUS'] = False

# config mysql
app.config['MYSQL_HOST'] = 'bdhcrxeh5wrrth7hjhl9-mysql.services.clever-cloud.com'
app.config['MYSQL_USER'] = 'uhgarfiobxjqzjyj'
app.config['MYSQL_PASSWORD'] = 'eQOlZxNjckNXCFd102nx'
app.config['MYSQL_DB'] = 'bdhcrxeh5wrrth7hjhl9'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# initialise
mysql = MySQL(app)


@app.route('/')
def home():
    return render_template('home.html')


class RegisterForm(Form):
    name = StringField('Name', [
        validators.DataRequired(),
        validators.Length(min=1, max=50)],
        render_kw={"placeholder": "name..."})
    email = StringField('Email', [
        validators.DataRequired(),
        validators.Length(min=6, max=50)],
        render_kw={"placeholder": "email..."})
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.Length(min=6, max=50),
        validators.EqualTo('confirm', message='Passwords do not match')], render_kw={"placeholder": "password..."})
    confirm = PasswordField('Confirm Password', [validators.DataRequired()], render_kw={
        "placeholder": "confirm password..."})


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()

        myresult = cur.execute(
            "SELECT * FROM users WHERE email = %s", [email])

        if myresult > 0:
            flash('Sorry, user already registered. Try a new email.', 'warning')
            return redirect(url_for('register'))

        cur.execute(
            "INSERT INTO users(name, email, password) VALUES(%s, %s, %s)", (name, email, password))
        # Commit to DB
        mysql.connection.commit()
        # Close Connection
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        email = request.form['email']
        password_can = request.form['password']

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])

        if result > 0:
            data = cur.fetchone()
            password = data['password']
            id = data['id']

            if sha256_crypt.verify(password_can, password):
                session['logged_in'] = True
                session['id'] = id

                return redirect(url_for('dashboard'))
            else:
                error = 'Invalide login'
                return render_template('login.html', error=error)

        else:
            error = 'Email not found'
            return render_template('login.html', error=error)
        cur.close()

    return render_template('login.html')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route("/logout")
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')


@app.route('/gettask/<string:list_id>/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@is_logged_in
def gettask(list_id):
    cur = mysql.connection.cursor()
    user_id = session['id']
    cur.execute("SELECT * FROM tasks WHERE user_id = %s AND list_id = %s",
                (int(user_id), list_id))
    tasks = cur.fetchall()
    return json_response(tasks=tasks)


@app.route('/task', methods=['POST', 'PUT'])
@is_logged_in
def task():
    # initialize cursor
    cur = mysql.connection.cursor()
    list_id = 1
    body = request.get_json()
    if request.method == 'POST':
        # get data
        body = request.get_json()
        user_id = session["id"]
        list_id = body["list_id"]
        content = body["content"]

        # mysgl stuff
        cur.execute("INSERT INTO tasks( user_id, list_id, status, content) VALUES(%s, %s, %r, %s)",
                    (int(user_id), int(list_id), False, content))

        mysql.connection.commit()
    elif request.method == 'PUT':
        body = request.get_json()
        user_id = session["id"]
        list_id = body["list_id"]
        task_id = body["task_id"]

        cur.execute(
            "UPDATE tasks SET status = NOT status WHERE id = %s", [int(task_id)])
        mysql.connection.commit()

        cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND list_id = %s AND status = 0",
                    (int(user_id), list_id))
        count = cur.fetchone()['COUNT(*)']

        return json_response(counter=count)

    cur.close()
    return redirect('/gettask/%s/' % list_id)


@app.route('/cleartask', methods=['DELETE'])
@is_logged_in
def cleartasks():
    cur = mysql.connection.cursor()
    list_id = request.get_json()["list_id"]
    user_id = session["id"]
    print(list_id, user_id)
    cur.execute(
        "DELETE FROM tasks WHERE list_id = %s AND user_id = %s AND status = 1", (int(list_id), int(user_id)))

    mysql.connection.commit()
    cur.close()

    return redirect('/gettask/%s/' % list_id)


@app.route('/getlists', methods=['GET', 'POST', 'PUT', 'DELETE'])
@is_logged_in
def getlist():
    cur = mysql.connection.cursor()
    user_id = session["id"]

    qurey = "SELECT * FROM lists WHERE user_id = '%d'" % user_id

    cur.execute(qurey)
    lists = cur.fetchall()
    return json_response(lists=lists)


@app.route('/list', methods=['POST', 'DELETE'])
@is_logged_in
def list():
    # initialize cursor
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        # get data
        body = request.get_json()
        user_id = session["id"]
        list_title = body["list_title"]

        # mysgl stuff
        cur.execute("INSERT INTO lists( user_id, title) VALUES(%s, %s)",
                    (int(user_id), list_title))

        mysql.connection.commit()
    else:
        list_id = request.get_json()["list_id"]
        user_id = session["id"]

        cur.execute(
            "DELETE FROM tasks WHERE list_id=%s AND user_id=%s", (int(list_id), int(user_id)))
        mysql.connection.commit()
        cur.execute(
            "DELETE FROM lists WHERE id=%s AND user_id=%s", (int(list_id), int(user_id)))
        mysql.connection.commit()
    cur.close()
    return redirect('/getlists')


if __name__ == '__main__':
    app.debug = True
    app.run()
