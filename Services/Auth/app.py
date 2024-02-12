from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, g, abort
from waitress import serve
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
app.secret_key = os.environ.get('SECRET_KEY',os.urandom(24))
PRAGMA = 'PRAGMA key="{}"'.format(os.environ.get('DB_KEY'))

tokenExpirySeconds = 60 * 60

# Connect to database
conn = sqlite3.connect('database.db')
conn.execute(PRAGMA)
print('Connected to database')

# Initialise db 
# Create uuid function
conn.execute('CREATE TABLE IF NOT EXISTS users (id uuid primary key not null, username text not null, hash text not null, token text, expiry int, permissions int default 1)')
print('Table created successfully')

conn.execute('CREATE TABLE IF NOT EXISTS sso (id uuid primary key not null, token text not null, redirect text not null, application_id uuid not null, expiry int not null)')
print('Table created successfully')

conn.execute('CREATE TABLE IF NOT EXISTS applications (id uuid primary key not null, name text not null, key text not null unique)')
print('Table created successfully')

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
conn.execute('UPDATE users SET permissions = 7 WHERE username = "doctor"')
conn.execute('UPDATE users SET permissions = 11 WHERE username = "finance"')
conn.execute('UPDATE users SET permissions = 19 WHERE username = "hr"')
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
    print(password_hash)
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

@app.route('/')
def index():
    if session.get('auth_token') is None:
        return render_template('index.html')
    else:
        # Check if token is valid
        user = get_user_by_token(session.get('auth_token'))
        if user is not None:
            user = {'id': user[0], 'username': user[1], 'permissions': user[5]}
            return render_template('index.html', user=user)
        else:
            session.pop('auth_token', None)
            return render_template('index.html')

@app.route('/auth/login')
def login_page():
    # Check if user is loggedin
    # Check query paramaters for sso login token
    # if token is not present, render login page
    # if token is present, check if token is valid
    user = get_user_by_token(session.get('auth_token'))
    sso_token = request.args.get('token')
    if user is not None:
        # User is already logged in
        if sso_token is None:
            return redirect(url_for('index'))
        else:
            if check_sso_token(sso_token):
                # sso token is valid
                # Create application token
                application_token = os.urandom(24).hex()
                sso_token = get_and_revoke_sso_token(sso_token)
                conn = sqlite3.connect('database.db')
                conn.execute(PRAGMA)
                conn.execute('INSERT INTO application_tokens (id,application_id, token, user_id,expiry) VALUES (?,?, ?, ?,?)', (str(uuid.uuid4()), sso_token[3], str(application_token), user[0], time.time() + tokenExpirySeconds))
                conn.commit()
                conn.close()
                return redirect(url_for('redirect_sso', url=sso_token[2] + "?token=" + str(application_token)), code=302)
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
        session['auth_token'] = user_token
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
    if session.get('auth_token') is not None:
        user = get_user_by_token(session.get('auth_token'))
        if user is None:
            session.pop('auth_token', None)
            flash('Logged out successfully')
            return redirect(url_for('login'))
        conn = sqlite3.connect('database.db')
        conn.execute(PRAGMA)
        conn.execute('UPDATE users SET token=?, expiry=? WHERE token=?', (None, None, session.get('auth_token')))
        print(user[1])
        conn.execute('DELETE FROM application_tokens WHERE user_id=?', (str(user[0]),))
        conn.commit()
        conn.close()
        session.pop('auth_token', None)
        flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/auth/sso/generateToken', methods=['POST'])
def generate_sso_token():
    req_data = request.form 
    print(req_data)
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
    print(req_data)
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
    print(req_data)
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

if __name__ == '__main__':
    if os.environ.get('DEBUG', False):
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        serve(app, host='0.0.0.0', port=5000)
