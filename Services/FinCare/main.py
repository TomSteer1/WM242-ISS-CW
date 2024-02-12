from flask import Flask, render_template, request, redirect, url_for, flash, sessions, Blueprint
from auth import *
from app import sso_name, sso_key
subapp = Blueprint('main', __name__)

conn = sqlite3.connect('database.db')
print("Opened database successfully")

@subapp.route('/finances')
def finances():
    if checkPermission(8):
        return "Hello World"
    else:
        flash("Access Denied","failure")
        session.pop('token')
        return redirect(url_for('index'))

