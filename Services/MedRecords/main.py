from flask import Flask, render_template, request, redirect, url_for, flash, sessions, Blueprint
from auth import *
from app import sso_name, sso_key
subapp = Blueprint('main', __name__)

conn = sqlite3.connect('database.db')

@subapp.route('/records')
def records():
    return "Hello World"
    return render_template('records.html')
