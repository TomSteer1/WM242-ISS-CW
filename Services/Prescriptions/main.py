from flask import Flask, render_template, request, redirect, url_for, flash, sessions, Blueprint
from auth import *
from app import sso_name, sso_key, PRAGMA
from faker import Faker
import uuid
subapp = Blueprint('main', __name__)

conn = sqlite3.connect('database.db')
conn.execute(PRAGMA)
conn.execute("CREATE TABLE IF NOT EXISTS medicines (id uuid PRIMARY KEY, name TEXT, price REAL)")
conn.execute("CREATE TABLE IF NOT EXISTS prescriptions (id uuid PRIMARY KEY, user_id TEXT, medicine_id text, quantity INTEGER, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(medicine_id) REFERENCES medicines(id))")
conn.execute("CREATE TABLE IF NOT EXISTS demoSTATUS (user_ID TEXT, generated BOOLEAN, FOREIGN KEY(user_ID) REFERENCES users(id))")
conn.execute("CREATE TABLE IF NOT EXISTS patients (id uuid PRIMARY KEY, name TEXT)")
conn.commit()
conn.close()

def getMedicine(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute("SELECT * FROM medicines WHERE id=?", (id,))
    medicine = cursor.fetchone()
    conn.close()
    return medicine

def getMedicines():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute("SELECT * FROM medicines")
    medicines = cursor.fetchall()
    conn.close()
    return medicines

def listPatients():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    conn.close()
    return patients

def getPatient(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute("SELECT * FROM patients WHERE id=?", (id,))
    patient = cursor.fetchone()
    conn.close()
    return patient

def getPatientPrescriptions(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute("SELECT * FROM prescriptions JOIN medicines ON prescriptions.medicine_id = medicines.id WHERE user_id=?", (id,))
    prescriptions = cursor.fetchall()
    conn.close()
    return prescriptions



@subapp.route('/my-prescriptions')
@authRequired(1)
def my_prescriptions():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    user = getUser(session['token'])
    cursor = conn.execute("SELECT * FROM patients WHERE id=?", (user["id"],))
    patient = cursor.fetchone()
    if(patient is None):
        conn.execute("INSERT INTO patients (id, name) VALUES (?, ?)", (user["id"], user["username"]))
        conn.commit()
    cursor = conn.execute("SELECT * FROM demoSTATUS WHERE user_ID=?", (user["id"],))
    demo = cursor.fetchone()
    if(demo is None or demo[1] is False):
        fake = Faker()
        conn.execute("INSERT INTO prescriptions (id, user_id, medicine_id, quantity) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), user["id"], str(1), fake.random_int(1, 10)))
        conn.execute("INSERT INTO prescriptions (id, user_id, medicine_id, quantity) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), user["id"], str(2), fake.random_int(1, 10)))
        conn.execute("INSERT INTO prescriptions (id, user_id, medicine_id, quantity) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), user["id"], str(3), fake.random_int(1, 10)))
        conn.execute("INSERT INTO demoSTATUS (user_ID, generated) VALUES (?, ?)", (user["id"], True))
        conn.commit()
    conn.close()
    return render_template('my-prescriptions.html', prescriptions=getPatientPrescriptions(user["id"]), user=user)

@subapp.route('/patientss')
@authRequired(4) # Doctor
def list_patients():
    return render_template('list-patients.html', patients=listPatients(), user=getUser(session['token']), checkPermission=checkPermission)

@subapp.route('/medicines')
@authRequired(4) # Doctor
def list_medicines():
    return render_template('list-medicines.html', medicines=getMedicines(), user=getUser(session['token']), admin=checkPermission(36))


@subapp.route('/patient/<id>')
@authRequired(4) # Doctor
def view_patient(id):
    return render_template('view-patient.html', user=getUser(session['token']), prescriptions=getPatientPrescriptions(id), patient=getPatient(id), medications=getMedicines())  

@subapp.route('/medicine/add', methods=['POST'])
@authRequired(36) # Staff and Admin
def add_medicine():
    if 'name' not in request.form or 'price' not in request.form:
        flash('Please fill out the form', 'error')
        return redirect(url_for('main.list_medicines'))
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("INSERT INTO medicines (id, name, price) VALUES (?, ?, ?)", (str(uuid.uuid4()), request.form['name'], request.form['price']))
    conn.commit()
    conn.close()
    flash('Medicine added successfully', 'success')
    return redirect(url_for('main.list_medicines'))

@subapp.route('/medicine/delete', methods=['POST'])
@authRequired(36) # Staff and Admin
def delete_medicine():
    if 'id' not in request.form:
        flash('Please fill out the form', 'error')
        return redirect(url_for('main.list_medicines'))
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("DELETE FROM medicines WHERE id=?", (request.form['id'],))
    conn.commit()
    conn.close()
    flash('Medicine deleted successfully', 'success')
    return redirect(url_for('main.list_medicines'))

@subapp.route('/prescription/delete', methods=['POST'])
@authRequired(4) # Doctor
def delete_prescription():
    if 'id' not in request.form:
        flash('Please fill out the form', 'error')
        if request.referrer is None:
            return redirect(url_for('main.list_patients'))
        return redirect(request.referrer)
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute("SELECT * FROM prescriptions WHERE id=?", (request.form['id'],))
    prescription = cursor.fetchone()
    conn.execute("DELETE FROM prescriptions WHERE id=?", (request.form['id'],))
    conn.commit()
    conn.close()
    flash('Prescription deleted successfully', 'success')
    return redirect(url_for('main.view_patient', id=prescription[1]))

@subapp.route('/prescription/add', methods=['POST'])
@authRequired(4) # Doctor
def add_prescription():
    if 'patient_id' not in request.form or 'medicine_id' not in request.form or 'quantity' not in request.form:
        flash('Please fill out the form', 'error')
        return redirect(url_for('main.view_patient', id=request.form['patient_id']))
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("INSERT INTO prescriptions (id, user_id, medicine_id, quantity) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), request.form['patient_id'], request.form['medicine_id'], request.form['quantity']))
    conn.commit()
    conn.close()
    flash('Prescription added successfully', 'success')
    return redirect(url_for('main.view_patient', id=request.form['patient_id']))


# Demo data
if os.path.exists('initial') is False:
    with open("initial","w") as f:
        f.write("done")
    fake = Faker()
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("INSERT INTO medicines (id, name, price) VALUES (?, ?, ?)", (str(1), "Paracetamol", fake.random_int(1, 100)))
    conn.execute("INSERT INTO medicines (id, name, price) VALUES (?, ?, ?)", (str(2), "Melatonin", fake.random_int(1, 100)))
    conn.execute("INSERT INTO medicines (id, name, price) VALUES (?, ?, ?)", (str(3), "Methylphenidate", fake.random_int(1, 100)))
    conn.commit()
    conn.close()

