from flask import Flask, render_template, request, redirect, url_for, flash, sessions, Blueprint
from auth import *
from app import sso_name, sso_key
from faker import Faker
subapp = Blueprint('main', __name__)

# Create tables
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, date DATE, record TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS appointments (id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, date DATE, time TIME, doctor TEXT)")
conn.commit()
conn.close()

@subapp.route('/my-records')
def records():
    if 'token' not in session:
        return redirect(url_for('login'))
    user = getUser(session['token'])
    if user is None:
        return redirect(url_for('login'))
    if checkPermission(1):
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM records WHERE userid = ?", (user['id'],))
        records = cur.fetchall()
        conn.close()
        print(records)
        return render_template('records.html', records=records)
    else:
        return "Permission Denied", 403

@subapp.route('/my-gp')
def gp():
    if 'token' not in session:
        return redirect(url_for('login'))
    user = getUser(session['token'])
    if user is None:
        return redirect(url_for('login'))
    if checkPermission(1):
        fake = Faker()
        return render_template('gp.html', gp_name=fake.name(), gp_address=fake.address(), gp_phone=fake.phone_number())
    else:
        return "Permission Denied", 403

@subapp.route('/my-appointments')
def appointment():
    if 'token' not in session:
        return redirect(url_for('login'))
    user = getUser(session['token'])
    if user is None:
        return redirect(url_for('login'))
    if checkPermission(1):
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM appointments WHERE userid = ?", (user['id'],))
        appointments = cur.fetchall()
        conn.close()
        # Generate fake doctors using Faker
        fake = Faker()
        doctors = [ fake.name() for i in range(0, 10) ]
        return render_template('appointments.html', appointments=appointments, doctors=doctors)
    else:
        return "Permission Denied", 403

@subapp.route('/staff-records')
def staffRecords():
    if 'token' not in session:
        return redirect(url_for('login'))
    user = getUser(session['token'])
    if user is None:
        return redirect(url_for('login'))
    if checkPermission(4):
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM records")
        records = cur.fetchall()
        conn.close()
        return render_template('records.html', records=records)
    else:
        return "Permission Denied", 403

@subapp.route('/staff-appointments')
def staffAppointments():
    if 'token' not in session:
        return redirect(url_for('login'))
    user = getUser(session['token'])
    if user is None:
        return redirect(url_for('login'))
    if checkPermission(4):
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM appointments")
        appointments = cur.fetchall()
        conn.close()
        # Generate fake doctors using Faker
        fake = Faker()
        doctors = [ fake.name() for i in range(0, 10) ]
        return render_template('appointments.html', appointments=appointments, doctors=doctors)
    else:
        return "Permission Denied", 403

@subapp.route('/my-appointments/add', methods=['POST'])
def addAppointment():
    data = request.form
    if 'date' not in data or 'time' not in data or 'doctor' not in data:
        return "Missing fields", 400
    if 'token' not in session:
        return redirect(url_for('login'))
    user = getUser(session['token'])
    print(user)
    if user is None:
        return redirect(url_for('login'))
    if checkPermission(1):
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO appointments (userid, date, time, doctor) VALUES (?, ?, ?, ?)", (user['id'], request.form['date'], request.form['time'], request.form['doctor']))
        conn.commit()
        conn.close()
        return redirect(url_for('main.appointment'))
    else:
        return "Permission Denied", 403

@subapp.route('/my-prescriptions')
def prescriptions():
    return redirect("https://prescriptions.meditech.com/my-prescriptions")
