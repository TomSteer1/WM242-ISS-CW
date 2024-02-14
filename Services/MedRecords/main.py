from flask import Flask, render_template, request, redirect, url_for, flash, sessions, Blueprint, jsonify
from auth import *
from app import sso_name, sso_key, PRAGMA
from faker import Faker
import uuid
import datetime
subapp = Blueprint('main', __name__)

conn = sqlite3.connect('database.db')
conn.execute(PRAGMA)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS records (id uuid PRIMARY KEY, patientid TEXT, date DATE, record TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS patients (id uuid PRIMARY KEY, userid TEXT, name TEXT)")
conn.commit()
conn.close()


def findPatients(nameQuery):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE name LIKE ?",('%' + nameQuery + '%',))
    patients = cur.fetchall()
    conn.close()
    return patients

def getPatient(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE id = ?",(id,))
    patient = cur.fetchone()
    conn.close()
    return patient

def getPatientRecords(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM records WHERE patientid = ?",(id,))
    records = cur.fetchall()
    conn.close()
    return records

def getRecord(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM records WHERE id = ?",(id,))
    record = cur.fetchone()
    conn.close()
    return record

def addPatient(name,userid):
    id = str(uuid.uuid4())
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("INSERT INTO patients (id,userid,name) VALUES (?,?,?)",(id,userid,name))
    conn.commit()
    conn.close()
    return id

def addRecord(patientid,date,record):
    id = str(uuid.uuid4())
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("INSERT INTO records (id,patientid,date,record) VALUES (?,?,?,?)",(id,patientid,date,record))
    conn.commit()
    conn.close()
    return id


@subapp.route('/records')
def records():
    return render_template('records.html')

@subapp.route("/searchPatient")
@authRequired(4)
def searchPatient():
    query = request.args.get('query')
    if query == "":
        flash("Please enter a name to search for")
        return jsonify({"error": "Please enter a name to search for"}),400
    patients = findPatients(query)
    if len(patients) > 0 :
        return jsonify({"patients": patients,"error":None}),200
    else:
        return jsonify({"error": "No patient found"}),404


@subapp.route("/patient/<id>")
@authRequired(4)
def openPatient(id):
    if id is None:
        return redirect(url_for("app.index"))
    patient = getPatient(id)
    if patient is None:
        return redirect(url_for("app.index"))
    return render_template("patient.html",patient=patient,user=getUser(session['token']),records=getPatientRecords(patient[0]))


@subapp.route("/createPatient",methods=["POST"])
@authRequired(4)
def createPatientRoute():
    name = request.form.get("name")
    userid = request.form.get("userid")
    if name == "":
        flash("Please enter a name")
        return redirect(url_for("app.index"))
    if userid == "":
        flash("Please enter a userid")
        return redirect(url_for("app.index"))
    id = addPatient(name,userid)
    return redirect(url_for("main.openPatient",id=id))

@subapp.route("/addRecord?id=<id>",methods=["POST"])
@authRequired(4)
def addRecordRoute(id):
    record = request.form.get("record")
    if record == "":
        flash("Please enter a record")
        return redirect(url_for("main.openPatient",id=id))
    patient = getPatient(id)
    if patient is None:
        flash("Patient does not exist")
        return redirect(url_for("app.index",id=id))
    addRecord(id,datetime.datetime.now().strftime("%Y-%m-%d"),record)
    return redirect(url_for("main.openPatient",id=id))

@subapp.route("/deleteRecord?id=<id>",methods=["POST"])
@authRequired(4)
def deleteRecordRoute(id):
    recordid = request.form.get("recordid")
    record = getRecord(id)
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("DELETE FROM records WHERE id = ?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for("main.openPatient",id=record[1]))
    
@subapp.route("/deletePatient?id=<id>",methods=["POST"])
@authRequired(4)
def deletePatientRoute(id):
    patient = getPatient(id)
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("DELETE FROM patients WHERE id = ?",(id,))
    conn.execute("DELETE FROM records WHERE patientid = ?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for("app.index"))

## Set up demo data by checking if initlal file exists and if not create dat
if not os.path.exists("initial"):
    with open("initial","w") as f:
        f.write("done")
    if getPatient("1") is None:
        fake = Faker()
        p1 = addPatient(fake.name(),1)
        p2 = addPatient(fake.name(),2)
        p3 = addPatient(fake.name(),3)
        addRecord(p1,"2020-01-01",fake.text())
        addRecord(p1,"2020-01-02",fake.text())
        addRecord(p2,"2020-01-01",fake.text())
        addRecord(p2,"2020-01-02",fake.text())
        addRecord(p3,"2020-01-01",fake.text())
        addRecord(p3,"2020-01-02",fake.text())
