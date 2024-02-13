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

@subapp.route('/my-records')
@authRequired()
def records():
    user = getUser(session['token'])
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM records WHERE userid = ?", (user['id'],))
    records = cur.fetchall()
    conn.close()
    return render_template('records.html', records=records)

@subapp.route('/my-gp')
@authRequired()
def gp():
    fake = Faker()
    user = getUser(session['token'])
    return render_template('gp.html', gp_name=fake.name(), gp_address=fake.address(), gp_phone=fake.phone_number())

@subapp.route('/my-appointments')
@authRequired(1)
def appointment():
    user = getUser(session['token'])
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM appointments WHERE userid = ?", (user['id'],))
    appointments = cur.fetchall()
    conn.close()
    # Generate fake doctors using Faker
    fake = Faker()
    doctors = [ fake.name() for i in range(0, 10) ]
    return render_template('appointments.html', appointments=appointments, doctors=doctors)

@subapp.route('/staff-records')
@authRequired(4)
def staffRecords():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM records")
    records = cur.fetchall()
    conn.close()
    return render_template('records.html', records=records)

@subapp.route('/staff-appointments')
@authRequired(4)
def staffAppointments():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM appointments")
    appointments = cur.fetchall()
    conn.close()
    # Generate fake doctors using Faker
    fake = Faker()
    doctors = [ fake.name() for i in range(0, 10) ]
    return render_template('staff-appointments.html', appointments=appointments)

@subapp.route('/my-appointments/add', methods=['POST'])
@authRequired(1)
def addAppointment():
    data = request.form
    if 'date' not in data or 'time' not in data or 'doctor' not in data:
        return "Missing fields", 400
    user = getUser(session['token'])
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("INSERT INTO appointments (userid, date, time, doctor) VALUES (?, ?, ?, ?)", (user['id'], request.form['date'], request.form['time'], request.form['doctor']))
    conn.commit()
    conn.close()
    return redirect(url_for('main.appointment'))

@subapp.route('/my-prescriptions')
@authRequired(1)
def prescriptions():
    return redirect("https://prescriptions.meditech.com/my-prescriptions")
