from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, g, abort
from waitress import serve
from functools import wraps
import uuid
import os
import time
import hashlib
import secrets
import base64
from dotenv import load_dotenv
from sqlcipher3 import dbapi2 as sqlite3

load_dotenv()

app = Flask(__name__)

# Set secret key
app.secret_key = os.environ.get('SECRET_KEY',secrets.token_hex(32))
PRAGMA = 'PRAGMA key="{}"'.format(os.environ.get('DB_KEY'))

tokenExpirySeconds = 60 * 60

# Connect to database
conn = sqlite3.connect('database.db')
conn.execute(PRAGMA)

# Initialise db 
# Create uuid function
conn.execute('CREATE TABLE IF NOT EXISTS users (id uuid primary key not null, username text not null, hash text not null, token text, expiry int, permissions int default 1)')

conn.execute('CREATE TABLE IF NOT EXISTS sso (id uuid primary key not null, token text not null, redirect text not null, application_id uuid not null, expiry int not null)')

conn.execute('CREATE TABLE IF NOT EXISTS applications (id uuid primary key not null, name text not null, key text not null unique)')

conn.execute('CREATE TABLE IF NOT EXISTS application_tokens (id uuid primary key not null, application_id uuid not null, token text not null, user_id uuid not null, expiry int not null)')

## Insert Default Keys if they don't exist
# MedRecords
conn.execute('INSERT OR IGNORE INTO applications (id, name, key) VALUES (?, ?, ?)', (str(uuid.uuid4()), 'MedRecords', 'MedRecords'))
# CareConnect
conn.execute('INSERT OR IGNORE INTO applications (id, name, key) VALUES (?, ?, ?)', (str(uuid.uuid4()), 'CareConnect', 'CareConnect'))
# FinCare
conn.execute('INSERT OR IGNORE INTO applications (id, name, key) VALUES (?, ?, ?)', (str(uuid.uuid4()), 'FinCare', 'FinCare'))
# MediCloud
conn.execute('INSERT OR IGNORE INTO applications (id, name, key) VALUES (?, ?, ?)', (str(uuid.uuid4()), 'MediCloud', 'MediCloud'))
# Portal
conn.execute('INSERT OR IGNORE INTO applications (id, name, key) VALUES (?, ?, ?)', (str(uuid.uuid4()), 'Portal', 'Portal'))
# Prescriptions
conn.execute('INSERT OR IGNORE INTO applications (id, name, key) VALUES (?, ?, ?)', (str(uuid.uuid4()), 'Prescriptions', 'Prescriptions'))
cur = conn.cursor()
cur.execute('SELECT * FROM applications')
conn.commit()
# Close connection
conn.close()

def check_sso_token(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(PRAGMA)
    cursor.execute('SELECT * FROM sso WHERE token=?', (token,))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[4] > time.time():
        return True
    else:
        return False

def get_and_revoke_sso_token(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(PRAGMA)
    cursor.execute('SELECT * FROM sso WHERE token=?', (token,))
    result = cursor.fetchone()
    # Remove token from database
    conn.execute('DELETE FROM sso WHERE token=?', (token,))
    conn.commit()
    conn.close()
    return result

def get_sso_token(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(PRAGMA)
    cursor.execute('SELECT * FROM sso WHERE token=?', (token,))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[4] > time.time():
        return result
    else:
        return None

def get_sso_app_by_token(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(PRAGMA)
    cursor.execute('SELECT * FROM applications JOIN sso ON applications.id = sso.application_id WHERE sso.token=?', (token,))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[7] > time.time():
        return result
    else:
        return None

def get_user(username):
    if username is None:
        return None
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(PRAGMA)
    cursor.execute('SELECT * FROM users WHERE username=?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result is not None:
        return result
    else:
        return None

def get_user_by_token(token):
    if token is None:
        return None
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(PRAGMA)
    cursor.execute('SELECT * FROM users WHERE token=?', (str(token),))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[4] > time.time():
        return result
    else:
        return None

def get_application_token(token):
    if token is None:
        return None
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(PRAGMA)
    cursor.execute('SELECT * FROM application_tokens WHERE token=?', (str(token),))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[4] > time.time():
        return result
    else:
        return None

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(32)
    assert salt and isinstance(salt, str) and "$" not in salt
    assert isinstance(password, str)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(os.environ.get('HASH_ITERATIONS',26000))
    )
    b64_hash = base64.b64encode(pw_hash).decode("ascii").strip()
    return "{}${}".format(salt, b64_hash)


def verify_password(password, password_hash):
    if (password_hash or "").count("$") != 1:
        return False
    salt, b64_hash = password_hash.split("$", 1)
    compare_hash = hash_password(password, salt)
    return secrets.compare_digest(password_hash, compare_hash)

def check_app(name, key):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(PRAGMA)
    cursor.execute('SELECT * FROM applications WHERE name=?', (name,))
    result = cursor.fetchone()
    conn.close()
    # Would implement hashing here but for simplicity the hash function is skipped
    if result is not None and result[2] == key:
        return True
    else:
        return False

permissionCache = {}
def checkPermission(permission=1):
    # 1 = User
    # 2 = All Staff
    # 4 = Medical Staff
    # 8  = Finance
    # 16 = HR
    # 32 = Admin
    user = None 
    if 'token' not in session:
        return False
    if session['token'] in permissionCache:
        if permissionCache[session['token']]['time'] > time.time():
            user = permissionCache[session['token']]['user']
    if user is None:
        user = get_user_by_token(session['token'])
        if user is None:
            return False
        user = {'id': user[0], 'username': user[1], 'permissions': user[5]}
        permissionCache[session['token']] = {'time': time.time() + 15, 'user': user}
    return user['permissions'] & permission == permission

# Decorator for checking if a user is logged in with optional permission parameter
def authRequired(permission=1):
    def outer_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session is None or 'token' not in session:
                return redirect(url_for('login', next=request.url))
            # Check if token is expired
            localUser = get_user_by_token(session['token'])
            if localUser is None or localUser[4] < time.time():
                return redirect(url_for('login', next=request.url))
            ## Use parameter
            if checkPermission(permission):
                return f(*args, **kwargs)
            else:
                flash("Permission Denied")
                return "Permission Denied", 403
        return decorated_function
    return outer_decorator


@app.route('/')
def index():
    if session.get('token') is None:
        return render_template('index.html')
    else:
        # Check if token is valid
        user = get_user_by_token(session.get('token'))
        if user is not None:
            user = {'id': user[0], 'username': user[1], 'permissions': user[5]}
            return render_template('index.html', user=user, checkPermission=checkPermission)
        else:
            session.pop('token', None)
            return render_template('index.html')

@app.route('/auth/login')
def login_page():
    # Check if user is loggedin
    # Check query paramaters for sso login token
    # if token is not present, render login page
    # if token is present, check if token is valid
    user = get_user_by_token(session.get('token'))
    sso_token = request.args.get('token')
    if user is not None:
        # User is already logged in
        if sso_token is None:
            return redirect(url_for('index'))
        else:
            if check_sso_token(sso_token):
                # sso token is valid
                # redirect to confirm page
                return redirect(url_for('confirm_page', token=sso_token))
            else:
                return 'Invalid token', 400
    else:
       if sso_token is None:
           return render_template('login.html')
       else:
           if check_sso_token(sso_token):
               return render_template('login.html', sso_token=sso_token)
           else:
               return 'Invalid token', 400

@app.route('/auth/confirm')
def confirm_page():
    sso_token = request.args.get('token')
    user = get_user_by_token(session.get('token'))
    if user is None or sso_token is None:
        return redirect(url_for('index')), 400
    app = get_sso_app_by_token(sso_token)
    if app is None:
        return redirect(url_for('index')), 400
    return render_template('confirm.html', sso_token=sso_token, app=app, user=user)

@app.route('/auth/confirm', methods=['POST'])
def confirm():
    req_data = request.form
    if req_data.get('sso_token') is None:
        return 'Invalid request', 400
    user = get_user_by_token(session.get('token'))
    if user is None:
        return 'Invalid token', 400
    app = get_sso_app_by_token(req_data.get('sso_token'))
    if app is None:
        return 'Invalid token', 400
    # Create application token
    application_token = secrets.token_hex(24)
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute('INSERT INTO application_tokens (id,application_id, token, user_id,expiry) VALUES (?,?, ?, ?,?)', (str(uuid.uuid4()), app[0], application_token, user[0], time.time() + tokenExpirySeconds))
    conn.commit()
    conn.close()
    return redirect(url_for('redirect_sso', url=app[5] + "?token=" + application_token), code=302)


@app.route('/auth/login', methods=['POST'])
def login():
    req_data = request.form
    if req_data.get('username') is None or req_data.get('password') is None:
        return 'Invalid request', 400
    if req_data.get('sso_token') is not None and check_sso_token(req_data.get('sso_token')) is False:
        return 'Invalid token', 400
    # Check if user exists
    user = get_user(req_data.get('username'))
    if user is None or verify_password(req_data.get('password'),user[2]) is False:
        return 'Invalid username or password', 401
    else:
        conn = sqlite3.connect('database.db')
        conn.execute(PRAGMA)
        # Create user token
        user_token = os.urandom(24).hex()
        session['token'] = user_token
        conn.execute('UPDATE users SET token=?, expiry=? WHERE id=?', (str(user_token), time.time() + tokenExpirySeconds, user[0]))
        conn.commit()
        if req_data.get('sso_token') is None:
            # Redirect user to application with token in query parameters
            conn.close()
            flash('Logged in successfully')
            return redirect(url_for('index'))
        # Get sso token
        sso_token = get_and_revoke_sso_token(req_data.get('sso_token'))
        # Create application token
        application_token = os.urandom(24).hex()
        conn.execute('INSERT INTO application_tokens (id,application_id, token, user_id,expiry) VALUES (?,?, ?, ?,?)', (str(uuid.uuid4()), sso_token[3], str(application_token), user[0], time.time() + tokenExpirySeconds))
        conn.commit()
        conn.close()
        # Redirect user to application with token in query parameters
        #return redirect(sso_token[2]  + "?token=" + str(application_token), code=302)
        return redirect(url_for('redirect_sso', url=sso_token[2] + "?token=" + str(application_token)), code=302)


@app.route('/auth/register')
def register_page():
    return render_template('register.html', sso_token=request.args.get('token'))

@app.route('/auth/register', methods=['POST'])
def register():
    req_data = request.form
    if req_data.get('username') is None or req_data.get('password') is None:
        return 'Invalid request', 400
    # Check if user exists
    user = get_user(req_data.get('username'))
    if user is not None:
        flash('User already exists')
        if req_data.get('sso_token') is None:
            return redirect(url_for('register_page'))
        else:
            return redirect(url_for('register_page') + '?token=' + req_data.get('sso_token'))
    else:
        # Create user
        conn = sqlite3.connect('database.db')
        conn.execute(PRAGMA)
        conn.execute('INSERT INTO users (id, username, hash) VALUES (?, ?, ?)', (str(uuid.uuid4()), req_data.get('username'), hash_password(req_data.get('password'))))
        conn.commit()
        conn.close()
        flash('User created successfully')
        return redirect(url_for('login'))


@app.route('/auth/logout')
def logout():
    if session.get('token') is not None:
        user = get_user_by_token(session.get('token'))
        if user is None:
            session.pop('token', None)
            flash('Logged out successfully')
            return redirect(url_for('login'))
        conn = sqlite3.connect('database.db')
        conn.execute(PRAGMA)
        conn.execute('UPDATE users SET token=?, expiry=? WHERE token=?', (None, None, session.get('token')))
        conn.execute('DELETE FROM application_tokens WHERE user_id=?', (str(user[0]),))
        conn.commit()
        conn.close()
        session.pop('token', None)
        flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/auth/sso/generateToken', methods=['POST'])
def generate_sso_token():
    req_data = request.form 
    # Check required parameters are present
    if req_data.get('application_name') is None or req_data.get('application_key') is None or req_data.get('redirect') is None:
        return jsonify({'success': False,'message': 'Invalid request'}), 400
    # Check the application secret matches the one in the database
    if check_app(req_data.get('application_name'),req_data.get('application_key')) is True:        
        # Generate token
        token = str(uuid.uuid4())
        # Insert token into database
        conn = sqlite3.connect('database.db')
        conn.execute(PRAGMA)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE name=?', (req_data.get('application_name'),))
        result = cursor.fetchone()
        cursor.execute('INSERT INTO sso (id, token, redirect, application_id,expiry) VALUES (?, ?, ?, ?,?)', (str(uuid.uuid4()), token, req_data.get('redirect'), result[0], time.time() + tokenExpirySeconds))
        conn.commit()
        conn.close()
        return jsonify({'success': True,'token': token})
    else:
        return jsonify({'success': False,'message': 'Invalid application credentials'}),400

@app.route('/auth/sso/validateToken', methods=['POST'])
def validate_sso_token():
    req_data = request.form
    # Check required parameters are present
    if req_data.get('token') is None or req_data.get('application_name') is None or req_data.get('application_key') is None:
        return jsonify({'valid': False,'message': 'Invalid request'}), 400
    # Check the application secret matches the one in the database
    if check_app(req_data.get('application_name'),req_data.get('application_key')) is True:       
        # Check if token is valid
        result = get_application_token(req_data.get('token'))
        conn = sqlite3.connect('database.db')
        conn.execute(PRAGMA)
        cursor = conn.cursor()
        if result is not None and result[4] > time.time():
            cursor.execute('SELECT * FROM users WHERE id=?', (result[3],))
            user = cursor.fetchone()
            conn.close()
            if user is None:
                return jsonify({'valid': False}), 401
            return jsonify({'valid': True, 'user' : {'id': user[0], 'username': user[1], 'permissions': user[5]}, 'expiry': result[4],'token': result[2]})
        else:
            return jsonify({'valid': False}), 401
    else:
        return jsonify({'valid': False}), 401


@app.route('/auth/sso/redirect', methods=['GET'])
def redirect_sso():
    url = request.args.get('url')
    return redirect(str(url), code=302)

@app.route('/auth/sso/logout', methods=['POST'])
def logout_sso():
    req_data = request.form
    if req_data.get('token') is None or req_data.get('application_name') is None or req_data.get('application_key') is None:
        return jsonify({'success': False,'message': 'Invalid request'}), 400
    if check_app(req_data.get('application_name'), req_data.get('application_key')) is False:
        return jsonify({'success': False,'message': 'Invalid application credentials'}), 401
    if get_application_token(req_data.get('token')) is None:
        return jsonify({'success': False,'message': 'Invalid token'}),400
    # Delete token from database
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute('DELETE FROM application_tokens WHERE token=?', (req_data.get('token'),))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/applications')
@authRequired(32)
def applications():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM applications')
    result = cursor.fetchall()
    conn.close()
    user = get_user_by_token(session['token'])
    user = {'id': user[0], 'username': user[1], 'permissions': user[5]}
    return render_template('applications.html', applications=result, user=user)

@app.route('/admin/applications/add', methods=['POST'])
@authRequired(32)
def add_application():
    req_data = request.form
    if req_data.get('name') is None or req_data.get('key') is None:
        return 'Invalid request', 400
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute('INSERT INTO applications (id, name, key) VALUES (?, ?, ?)', (str(uuid.uuid4()), req_data.get('name'), req_data.get('key')))
    conn.commit()
    conn.close()
    flash('Application added successfully')
    return redirect(url_for('applications'))

@app.route('/admin/applications/delete?id=<id>', methods=['GET'])
@authRequired(32)
def delete_application(id):
    if id is None:
        return 'Invalid request', 400
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute('DELETE FROM applications WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Application deleted successfully')
    return redirect(url_for('applications'))

@app.route('/hr/users')
@authRequired(16)
def users():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    result = cursor.fetchall()
    conn.close()
    user = get_user_by_token(session['token'])
    user = {'id': user[0], 'username': user[1], 'permissions': user[5]}
    return render_template('users.html', users=result, user=user)

@app.route('/hr/users/modify?id=<id>', methods=['POST'])
@authRequired(16)
def modifyUser(id):
    if id is None or 'permission' not in request.form:
        return 'Invalid request', 400
    if checkPermission(int(request.form['permission'])) is False:
        return 'Permission Denied', 403
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute('UPDATE users SET permissions=? WHERE id=?', (request.form['permission'], id))
    conn.commit()
    conn.close()
    flash('User modified successfully')
    return redirect(url_for('users'))


## Set up demo data by checking if initlal file exists and if not create data
if os.path.exists("initial") is False:
    with open("initial","w") as f:
        f.write("done")
   # Creates a user for each role
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    # Check if users table is empty
    cur.execute('SELECT * FROM users')
    result = cur.fetchone()
    if result is not None:
        conn.close()
    else:        
        # Patient
        conn.execute('INSERT INTO users (id, username, hash, permissions) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), 'patient', hash_password('patient'), 1))
        # Doctor
        conn.execute('INSERT INTO users (id, username, hash, permissions) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), 'doctor', hash_password('doctor'), 7))
        # Finance
        conn.execute('INSERT INTO users (id, username, hash, permissions) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), 'finance', hash_password('finance'), 11))
        # HR 
        conn.execute('INSERT INTO users (id, username, hash, permissions) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), 'hr', hash_password('hr'), 19))
        # Admin
        conn.execute('INSERT INTO users (id, username, hash, permissions) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), 'admin', hash_password('admin'), 31))
        # Superadmin
        conn.execute('INSERT INTO users (id, username, hash, permissions) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), 'superadmin', hash_password('superadmin'), 63))
        conn.commit()
        conn.close()


if __name__ == '__main__':
    if os.environ.get('DEBUG', False):
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        serve(app, host='0.0.0.0', port=5000)
