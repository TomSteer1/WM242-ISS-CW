from flask import Flask, render_template, request, redirect, url_for, flash, sessions, Blueprint
from auth import *
from app import sso_name, sso_key, PRAGMA
import uuid
from faker import Faker
subapp = Blueprint('main', __name__)

conn = sqlite3.connect('database.db')
conn.execute(PRAGMA)
# Transaction Table
conn.execute("CREATE TABLE IF NOT EXISTS transactions (id uuid PRIMARY KEY, date TEXT, description TEXT, amount REAL)")
conn.commit()
conn.close()


def listTransactions():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.execute("SELECT * FROM transactions ORDER BY DATE DESC")
    transactions = cursor.fetchall()
    conn.close()
    return transactions

@subapp.route('/listTransactions')
@authRequired(8)
def listTransactionsRoute():
    transactions = listTransactions()
    return render_template('transactions.html', transactions=transactions, user=getUser(session['token']),checkPermission=checkPermission)

@subapp.route('/addTransaction')
@authRequired(8)
def addTransactionRoute():
    return render_template('addTransaction.html')

@subapp.route('/addTransaction', methods=['POST'])
@authRequired(8)
def addTransactionRoutePost():
    if 'date' not in request.form or 'description' not in request.form or 'amount' not in request.form
        flash('Please fill out all fields')
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (id, date, description, amount) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), request.form['date'], request.form['description'], request.form['amount']))
    conn.commit()
    conn.close()
    flash('Transaction added successfully')
    return redirect(url_for('main.listTransactionsRoute'))

@subapp.route('/deleteTransaction?id=<id>', methods=['POST'])
@authRequired(32)
def deleteTransactionRoute(id):
    if id is None:
        flash('Please provide a transaction id')
        return redirect(url_for('main.listTransactionsRoute'))
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("DELETE FROM transactions WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash('Transaction deleted successfully')
    return redirect(url_for('main.listTransactionsRoute'))


# Demo data
if not os.path.exists('inital'):
    with open("initial","w") as f:
        f.write("done")
    fake = Faker()
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    for i in range(100):
        conn.execute("INSERT INTO transactions (id, date, description, amount) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), fake.date(), fake.company(), fake.random_int(1, 1000)))
    conn.commit()
    conn.close()
