# Description: Authentication functions for the SSO server
from flask import Flask, request, session, redirect, url_for
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
    print("Generating token")
    request = requests.post(sso_generateToken, data = {'application_name': sso_name, 'application_key': sso_key, 'redirect': sso_redirect}, verify=False)
    print(request.text)
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
        tokenRequest = requests.post(sso_logout, data = {'token': user[3], 'application_name': sso_name, 'application_key': sso_key},verify=False)
        print(tokenRequest.text)
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
        return tokenRequest.json()['user']

def handleCallback():
    token = request.args.get('token')
    # Validate the token
    tokenRequest = requests.post(sso_validateToken, data = {'token': token, 'application_name': sso_name, 'application_key': sso_key},verify=False)
    if tokenRequest.json()['valid']:
        session['token'] = generateToken(tokenRequest.json()['user']['id'],tokenRequest.json()['token'],tokenRequest.json()['expiry'])
        return redirect(url_for('index'))
    else:
        return "Login Failed", 401

def checkPermission(permissionBit):
    # 1 = User
    # 2 = All Staff
    # 4 = Medical Staff
    # 8  = Finance
    # 16 = HR
    # 32 = Admin
    user = None 
    for key in permissionCache:
        if permissionCache[key]['time'] < time.time():
            permissionCache.pop(key)
            break
        else:
            print("Cache hit")
            print(time.time())
            user = permissionCache[key]['user']
            break
    if user is None:
        user = getUser(session['token'])
        permissionCache[session['token']] = {'time': time.time() + 15, 'user': user}
        print("Cache miss")
        print(time.time())

    print("Checking permission bit " + str(permissionBit) + " for user " + str(user))
    if user is None:
        return False
    else:
        return user['permissions'] & permissionBit == permissionBit
