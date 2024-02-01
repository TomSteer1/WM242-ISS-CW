from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, g, abort
import sqlite3
import uuid
import os
import time

app = Flask(__name__)

# Set secret key
app.secret_key = os.urandom(24)

tokenExpirySeconds = 60 * 60

# Connect to database
conn = sqlite3.connect('database.db')
print('Connected to database')

# Initialise db 
# Create uuid function
conn.execute('CREATE TABLE IF NOT EXISTS users (id uuid primary key not null, username text not null, hash text not null, token text, expiry int, permissions int default 0)')
print('Table created successfully')

conn.execute('CREATE TABLE IF NOT EXISTS sso (id uuid primary key not null, token text not null, redirect text not null, application_id uuid not null, expiry int not null)')
print('Table created successfully')

conn.execute('CREATE TABLE IF NOT EXISTS applications (id uuid primary key not null, name text not null, key text not null)')
print('Table created successfully')

conn.execute('CREATE TABLE IF NOT EXISTS application_tokens (id uuid primary key not null, application_id uuid not null, token text not null, user_id uuid not null, expiry int not null)')

# Close connection
conn.close()

def check_sso_token(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sso WHERE token=?', (token,))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[4] > time.time():
        return True
    else:
        return False

def get_sso_token(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sso WHERE token=?', (token,))
    result = cursor.fetchone()
    # Remove token from database
    conn.execute('DELETE FROM sso WHERE token=?', (token,))
    conn.commit()
    conn.close()
    return result

def get_user(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result is not None:
        return result
    else:
        return None

def get_user_by_token(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE token=?', (str(token),))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[4] > time.time():
        return result
    else:
        return None

def get_application_token(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM application_tokens WHERE token=?', (token,))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[4] > time.time():
        return result
    else:
        return None

def hash_password(password):
    return password

def check_app(name, key):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM applications WHERE name=?', (name,))
    result = cursor.fetchone()
    conn.close()
    if result is not None and result[2] == hash_password(key):
        return True
    else:
        return False

@app.route('/')
def index():
    # Check if user is loggedin
    print(session.get('auth_token'))
    if session.get('auth_token') is None:
        return redirect(url_for('login'))
    else:
        # Check if token is valid
        user = get_user_by_token(session.get('auth_token'))
        if user is not None:
            return 'Hello ' + user[1]
        else:
            return redirect(url_for('login'))

@app.route('/auth/login')
def login():
    # Check query paramaters for sso login token
    # if token is invalid, return error
    sso_token = request.args.get('token')
    if sso_token is None:
        return 'Invalid token'
    else:
        # If token is valid, allow user to login
        # Else, return error
        if check_sso_token(sso_token):
            # Check if user is loggedin
            if session.get('auth_token') is not None:
                # Check if token is valid
                user = get_user_by_token(session.get('auth_token'))
                if user is not None:
                    # Redirect user to application with token in query parameters
                    application_token = uuid.uuid4()
                    conn = sqlite3.connect('database.db')
                    conn.execute('INSERT INTO application_tokens (id,application_id, token, user_id,expiry) VALUES (?,?, ?, ?,?)', (str(uuid.uuid4()), sso_token[3], str(application_token), user[0], time.time() + tokenExpirySeconds))
                    conn.commit()
                    conn.close()
                    # Redirect user to application with token in query parameters
                    sso_token = get_sso_token(sso_token)
                    return redirect(url_for('redirect_sso', url=sso_token[2] + "?token=" + str(application_token)), code=302)
                else:
                    # Render login page template
                    return render_template('login.html', sso_token=sso_token)
            # Render login page template
            return render_template('login.html', sso_token=sso_token)

        else:
            return 'Invalid token'

@app.route('/auth/login', methods=['POST'])
def api():
    req_data = request.form
    if req_data.get('username') is None or req_data.get('password') is None or req_data.get('sso_token') is None:
        return 'Invalid request'
    if check_sso_token(req_data.get('sso_token')) is False:
        return 'Invalid token'
    # Check if user exists
    user = get_user(req_data.get('username'))
    if user is None or user[2] != hash_password(req_data.get('password')):
        return 'Invalid username or password'
    else:
        # Get sso token
        sso_token = get_sso_token(req_data.get('sso_token'))
        conn = sqlite3.connect('database.db')
        # Create user token
        user_token = uuid.uuid4()
        session['auth_token'] = user_token
        conn.execute('UPDATE users SET token=?, expiry=? WHERE id=?', (str(user_token), time.time() + tokenExpirySeconds, user[0]))
        conn.commit()
        # Create application token
        application_token = uuid.uuid4()
        conn.execute('INSERT INTO application_tokens (id,application_id, token, user_id,expiry) VALUES (?,?, ?, ?,?)', (str(uuid.uuid4()), sso_token[3], str(application_token), user[0], time.time() + tokenExpirySeconds))
        conn.commit()
        conn.close()
        # Redirect user to application with token in query parameters
        #return redirect(sso_token[2]  + "?token=" + str(application_token), code=302)
        return redirect(url_for('redirect_sso', url=sso_token[2] + "?token=" + str(application_token)), code=302)


@app.route('/auth/register', methods=['POST'])
def register():
    req_data = request.get_json()
    print(req_data)
    return jsonify(req_data)

@app.route('/auth/logout', methods=['POST'])
def logout():
    req_data = request.get_json()
    print(req_data)
    return jsonify(req_data)

@app.route('/auth/sso/generateToken', methods=['POST'])
def generate_sso_token():
    req_data = request.form 
    print(req_data)
    # Check required parameters are present
    if req_data.get('application_name') is None or req_data.get('application_key') is None or req_data.get('redirect') is None:
        return jsonify({'success': False,'message': 'Invalid request'})
    # Check the application secret matches the one in the database
    if check_app(req_data.get('application_name'),req_data.get('application_key')) is True:        
        # Generate token
        token = str(uuid.uuid4())
        # Insert token into database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE name=?', (req_data.get('application_name'),))
        result = cursor.fetchone()
        cursor.execute('INSERT INTO sso (id, token, redirect, application_id,expiry) VALUES (?, ?, ?, ?,?)', (str(uuid.uuid4()), token, req_data.get('redirect'), result[0], time.time() + tokenExpirySeconds))
        conn.commit()
        conn.close()
        return jsonify({'success': True,'token': token})
    else:
        return jsonify({'success': False,'message': 'Invalid application credentials'})

@app.route('/auth/sso/validateToken', methods=['POST'])
def validate_sso_token():
    req_data = request.form
    print(req_data)
    # Check required parameters are present
    if req_data.get('token') is None or req_data.get('application_name') is None or req_data.get('application_key') is None:
        return jsonify({'valid': False,'message': 'Invalid request'})
    # Check the application secret matches the one in the database
    if check_app(req_data.get('application_name'),req_data.get('application_key')) is True:       
        # Check if token is valid
        result = get_application_token(req_data.get('token'))
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        if result is not None and result[4] > time.time():
            cursor.execute('SELECT * FROM users WHERE id=?', (result[3],))
            user = cursor.fetchone()
            conn.close()
            if user is None:
                return jsonify({'valid': False})
            return jsonify({'valid': True, 'user' : {'id': user[0], 'username': user[1], 'permissions': user[5]}, 'expiry': result[4],'token': result[2]})
        else:
            return jsonify({'valid': False})
    else:
        return jsonify({'valid': False})

@app.route('/auth/sso/redirect', methods=['GET'])
def redirect_sso():
    url = request.args.get('url')
    return redirect(str(url), code=302)

@app.route('/auth/sso/logout', methods=['POST'])
def logout_sso():
    req_data = request.form
    print(req_data)
    if req_data.get('token') is None or req_data.get('application_name') is None or req_data.get('application_key') is None:
        return jsonify({'success': False,'message': 'Invalid request'}, 400)
    if check_app(req_data.get('application_name'), req_data.get('application_key')) is False:
        return jsonify({'success': False,'message': 'Invalid application credentials'}, 401)
    if get_application_token(req_data.get('token')) is None:
        return jsonify({'success': False,'message': 'Invalid token'}, 401)
    # Delete token from database
    conn = sqlite3.connect('database.db')
    conn.execute('DELETE FROM application_tokens WHERE token=?', (req_data.get('token'),))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



