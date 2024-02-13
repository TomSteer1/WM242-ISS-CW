# Description: Authentication functions for the SSO server
from flask import Flask, request, session, redirect, url_for
from functools import wraps
import requests
import os
from sqlcipher3 import dbapi2 as sqlite3
from app import sso_name, sso_key, sso_redirect, PRAGMA
import time

# SSO server details
sso_generateToken = 'https://auth.meditech.com/auth/sso/generateToken'
sso_validateToken = 'https://auth.meditech.com/auth/sso/validateToken'
sso_login = 'https://auth.meditech.com/auth/login'
sso_logout = 'https://auth.meditech.com/auth/sso/logout'


## Cache for permission, caches for 15s
permissionCache = {}

def generateAuth():
    # Request a token from the SSO server
    request = requests.post(sso_generateToken, data = {'application_name': sso_name, 'application_key': sso_key, 'redirect': sso_redirect}, verify=False)
    if request.status_code != 200 or request.json()['success'] == False: 
        return False
    token = request.json()['token']
    # Redirect to the SSO server

    return sso_login + '?token=' + token

def generateToken(userID,sso_token,expiry=0):
    # Generate random md5 hash
    token = os.urandom(24).hex()
    # Insert the token into the database
    conn = sqlite3.connect('database.db')
    # Create user if they don't exist
    conn.execute(PRAGMA)
    conn.execute('INSERT OR IGNORE INTO users (sso_id) VALUES (?)', (userID,))
    conn.execute('UPDATE users SET user_token = ?, sso_token = ?, expiry = ? WHERE sso_id = ?', (token, sso_token, expiry, userID))
    conn.commit()
    conn.close()
    return token

def validateToken(token):
    if token is None:
        return False
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute('SELECT * FROM users WHERE user_token = ?', (token,))
    user = cursor.fetchone()
    conn.close()
    if user is None:
        return False
    else:
        tokenRequest = requests.post(sso_validateToken, data = {'token': user[3], 'application_name': sso_name, 'application_key': sso_key},verify=False)
        return tokenRequest.json()['valid']

def revokeToken(token):
    if token is None:
        return False
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute('SELECT * FROM users WHERE user_token = ?', (token,))
    user = cursor.fetchone()
    conn.close()
    if user is None:
        return False
    else:
        conn = sqlite3.connect('database.db')
        conn.execute(PRAGMA)
        conn.execute('UPDATE users SET user_token = ? , expiry = 0 WHERE user_token=?', (token,token))
        conn.commit()
        conn.close()
        tokenRequest = requests.post(sso_logout, data = {'token': user[3], 'application_name': sso_name, 'application_key': sso_key},verify=False)
        return tokenRequest.json()['success']

def getUser(token):
    if token is None:
        return None
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute('SELECT * FROM users WHERE user_token = ?', (token,))
    user = cursor.fetchone()
    conn.close()
    if user is None:
        return None
    else:
        tokenRequest = requests.post(sso_validateToken, data = {'token': user[3], 'application_name': sso_name, 'application_key': sso_key},verify=False)
        if tokenRequest.status_code != 200:
            return None
        return tokenRequest.json()['user']

def getLocalUser(token):
    if token is None:
        return None
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute('SELECT * FROM users WHERE user_token = ?', (token,))
    user = cursor.fetchone()
    conn.close()
    return user

def handleCallback():
    token = request.args.get('token')
    # Validate the token
    tokenRequest = requests.post(sso_validateToken, data = {'token': token, 'application_name': sso_name, 'application_key': sso_key},verify=False)
    if tokenRequest.json()['valid']:
        session['token'] = generateToken(tokenRequest.json()['user']['id'],tokenRequest.json()['token'],tokenRequest.json()['expiry'])
        return redirect(url_for('index'))
    else:
        flash("Login Failed")
        return redirect(url_for('index'))

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
        user = getUser(session['token'])
        if user is None:
            return False
        permissionCache[session['token']] = {'time': time.time() + 15, 'user': user}
    return user['permissions'] & permission == permission

# Decorator for checking if a user is logged in with optional permission parameter
def authRequired(permission=1):
    def outer_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'token' not in session:
                return redirect(url_for('login', next=request.url))
            # Check if token is expired
            if getLocalUser(session['token'])[4] < time.time():
                return redirect(url_for('login', next=request.url))
            ## Use parameter
            if 'permission' in kwargs:
                if checkPermission(kwargs['permission']):
                    return f(*args, **kwargs)
                else:
                    flash("Permission Denied")
                    return "Permission Denied", 403
            elif checkPermission(1):
                return f(*args, **kwargs)
            else:
                return "Permission Denied", 403
        return decorated_function
    return outer_decorator

