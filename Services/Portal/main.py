from flask import Flask, render_template, request, redirect, url_for, flash, sessions, Blueprint
from auth import *
from app import sso_name, sso_key, PRAGMA
from faker import Faker
subapp = Blueprint('main', __name__)

# Create tables
conn = sqlite3.connect('database.db')
conn.execute(PRAGMA)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, date DATE, record TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS appointments (id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, date DATE, time TIME, doctor TEXT)")
conn.commit()
conn.close()

@subapp.route('/portal')
def portal():
    if 'token' not in session:
        return redirect(url_for('index'))
    return render_template('portal.html', user=checkPermission(1),staff=checkPermission(2),medicalStaff=checkPermission(4), finance=checkPermission(8), hr=checkPermission(16), admin=checkPermission(32), name = getUser(session['token'])['username'])
