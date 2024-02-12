from flask import Flask, render_template, request, redirect, url_for, flash, session
from waitress import serve
from dotenv import load_dotenv
import os
import requests
import secrets
from sqlcipher3 import dbapi2 as sqlite3
from auth import *

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY',secrets.token_hex(32))

PRAGMA = 'PRAGMA key="{}"'.format(os.environ.get('DB_KEY'))


# SSO Config
sso_name = os.environ.get('SSO_NAME')
sso_key = os.environ.get('SSO_KEY')
sso_redirect = os.environ.get('SSO_REDIRECT')

def init():
    from main import subapp
    app.register_blueprint(subapp)
    
    # Initialize the database
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)

    # Create the table if it doesn't exist
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, sso_id TEXT NOT NULL UNIQUE, user_token TEXT, sso_token TEXT, expiry INT DEFAULT 0)')
    print("Users table created successfully")
    conn.commit()
    conn.close()


@app.route('/')
def index():
    # Check if the user is logged in
    if validateToken(session.get('token')) == False:
        return render_template('index.html', auth = False, checkPermission=checkPermission)
    else:
        if(checkPermission(1)):
            return render_template('index.html', auth = True, user = getUser(session.get('token')), checkPermission=checkPermission)
        else:
            flash("Access Denied")
            session.pop('token')
            return render_template('index.html', auth = False, checkPermission=checkPermission)

@app.route('/auth/login')
def login():
    print("Logging in")
    url = generateAuth()
    if url == False:
        return "Something went wrong", 500
    else:
        return redirect(url)

@app.route('/auth/logout')
def logout():
    if(validateToken(session.get('token')) == False):
        return redirect(url_for('index'))
    if revokeToken(session.get('token')) == True:
        session.pop('token', None)
        flash('You have successfully logged out', 'success')
        return redirect(url_for('index'))
    else:
        return "Something went wrong", 500

@app.route('/callback')
def callback():
    return handleCallback()

if __name__ == '__main__':
    init()
    if os.environ.get('DEBUG',False) == False:
        serve(app, port=5000, host='0.0.0.0')
    else:
        port = int(os.environ.get('APP_PORT', 5000))
        app.run(debug=bool(os.environ.get('DEBUG',False)), port=port, host='0.0.0.0')
