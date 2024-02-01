from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
import os
import requests
import sqlite3

from auth import *


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY',os.urandom(24))

# Load environment variables from .env file
load_dotenv()

# SSO Config
sso_name = os.environ.get('SSO_NAME')
sso_key = os.environ.get('SSO_KEY')
sso_redirect = os.environ.get('SSO_REDIRECT')

# Initialize the database
conn = sqlite3.connect('database.db')
print("Opened database successfully")

# Create the table if it doesn't exist
conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, sso_id TEXT NOT NULL, user_token TEXT, sso_token TEXT, expiry INT DEFAULT 0)')
print("Table created successfully")

conn.close()


@app.route('/')
def index():
    # Check if the user is logged in
    if validateToken(session.get('token')) == False:
        return render_template('index.html', auth = False)
    else:
        return render_template('index.html', auth = True, user = getUser(session.get('token')))

@app.route('/login')
def login():
    return redirect(generateAuth())

@app.route('/logout')
def logout():
    if(validateToken(session.get('token')) == False):
        return redirect(url_for('index'))
    if revokeToken(session.get('token')) == True:
        session.pop('token', None)
        flash('You have successfully logged out', 'success')
        return redirect(url_for('index'))
    else:
        return "Something went wrong"

@app.route('/callback')
def callback():
    return handleCallback()



if __name__ == '__main__':
    port = int(os.environ.get('APP_PORT', 5000))
    app.run(debug=True, port=port, host='0.0.0.0')
