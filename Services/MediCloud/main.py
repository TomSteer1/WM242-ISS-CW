from flask import Flask, render_template, request, redirect, url_for, flash, sessions, Blueprint, send_file
from auth import *
from app import sso_name, sso_key,PRAGMA
import uuid
import secrets
from io import BytesIO
from Crypto.Cipher import AES
subapp = Blueprint('main', __name__)

conn = sqlite3.connect('database.db')
print("Opened database successfully")
conn.execute(PRAGMA)
conn.execute("CREATE TABLE IF NOT EXISTS files (id uuid PRIMARY KEY, userid TEXT, filename TEXT, public BOOL DEFAULT 0, mimetype TEXT, shared BOOL DEFAULT 0)")
conn.execute("CREATE TABLE IF NOT EXISTS kms (id uuid PRIMARY KEY, key TEXT NOT NULL, iv TEXT NOT NULL)")
conn.commit()
conn.close()

def list_files():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM files")
    files = cur.fetchall()
    conn.close()
    return files

def list_user_files(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE userid=?",(id,))
    files = cur.fetchall()
    conn.close()
    return files

def list_public_files():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE public")
    files = cur.fetchall()
    conn.close()
    return files

def list_staff_files():
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE shared")
    files = cur.fetchall()
    conn.close()
    return files

def get_file(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE id=?",(id,))
    file = cur.fetchone()
    conn.close()
    return file

def get_key(id):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT * FROM kms WHERE id=?",(id,))
    key = cur.fetchone()
    conn.close()
    return key

def delete_file(fileId):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute("DELETE FROM files WHERE id=?",(fileId,))
    conn.execute("DELETE FROM kms WHERE id=?",(fileId,))
    conn.commit()
    conn.close()
    os.remove(os.path.join("uploads",fileId))

def toggle_public_file(fileId):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT public FROM files WHERE id=?",(fileId,))
    status = cur.fetchone()[0]
    status = not status
    conn.execute("UPDATE files SET public = ? WHERE id=?",(status,fileId))
    conn.commit()
    conn.close()

def toggle_shared_file(fileId):
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    cur = conn.cursor()
    cur.execute("SELECT shared FROM files WHERE id=?",(fileId,))
    status = cur.fetchone()[0]
    status = not status
    conn.execute("UPDATE files SET shared = ? WHERE id=?",(status,fileId))
    conn.commit()
    conn.close()

def encryptFile(file):
    key = secrets.token_bytes(16)
    cipher = AES.new(key,AES.MODE_CFB)
    iv = cipher.iv
    encData = cipher.encrypt(file.read())
    fileId = str(uuid.uuid4())
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute('INSERT INTO kms (id,key,iv) VALUES (?,?,?)',(fileId,key,iv))
    conn.commit()
    conn.close()
    fo = open(os.path.join("uploads",fileId),"wb")
    fo.write(encData)
    fo.close()
    return fileId

def decryptFile(encFile,key,iv):
    decrypt_cipher = AES.new(key, AES.MODE_CFB, iv)
    decFile = decrypt_cipher.decrypt(encFile)
    return decFile

def sendFile(dbFile):
    fileId = dbFile[0]
    key = get_key(fileId)
    fo = open(os.path.join("uploads",fileId),"rb")
    data = decryptFile(fo.read(),key[1],key[2])
    buffer = BytesIO()
    buffer.write(data)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=dbFile[2],
        mimetype=dbFile[4]
    )

@subapp.route('/files')
@authRequired(2)
def files():
    user = getUser(session['token'])
    return render_template('files.html', publicFiles=list_public_files(), user=user, files=list_user_files(user['id']), staffFiles=list_staff_files())

@subapp.route('/file/<fileId>')
def getFile(fileId):
    if fileId is None:
        return "Invalid Request",403
    dbFile = get_file(fileId)    
    if dbFile is None:
        return "File not found",404
    if dbFile[3] == True:
        return sendFile(dbFile)
    if checkPermission(2) is False:
        return "File not found",404
    if dbFile[5] == True:
        return sendFile(dbFile)
    user = getUser(session['token'])
    if dbFile[1] != user['id']:
        return "File not found",404
    return sendFile(dbFile)


@subapp.route('/deleteFile',methods=['POST'])
@authRequired(2)
def deleteFile():
    if 'id' not in request.form:
        return "Invalid Request",403
    dbFile = get_file(request.form['id'])
    if dbFile is None:
        return "File not found",404
    user = getUser(session['token'])
    if dbFile[1] != user['id']:
        return "Invalid Permissions",200
    delete_file(request.form['id'])
    return "File Deleted",200

@subapp.route('/togglePublic',methods=['POST'])
@authRequired(2)
def togglePublicFile():
    if 'id' not in request.form:
        return "Invalid Request",403
    dbFile = get_file(request.form['id'])
    if dbFile is None:
        return "File not found",404
    user = getUser(session['token'])
    if dbFile[1] != user['id']:
        return "Invalid Permissions",200
    toggle_public_file(request.form['id'])
    return "File Status Changed",200

@subapp.route('/toggleShared',methods=['POST'])
@authRequired(2)
def toggleSharedFile():
    if 'id' not in request.form:
        return "Invalid Request",403
    dbFile = get_file(request.form['id'])
    if dbFile is None:
        return "File not found",404
    user = getUser(session['token'])
    if dbFile[1] != user['id']:
        return "Invalid Permissions",200
    toggle_shared_file(request.form['id'])
    return "File Status Changed",200


@subapp.route('/uploadFile', methods=['POST'])
@authRequired(2)
def uploadFile():
    if 'file' not in request.files:
        return "No file uploaded",403
    fileID = str(uuid.uuid4())
    while get_file(fileID) is not None:
        fileID = str(uuid.uuid4())
    file = request.files['file']
    public = False
    shared = False
    if 'public' in request.form:
        if request.form['public'] == "on":
            public = True
    if 'shared' in request.form:
        if request.form['shared'] == "on":
            shared = True
    fileID = encryptFile(file)
    conn = sqlite3.connect('database.db')
    conn.execute(PRAGMA)
    conn.execute('INSERT INTO files (id,userid,filename,public,mimetype,shared) VALUES (?,?,?,?,?,?)',(fileID,getUser(session['token'])['id'],file.filename,public,file.mimetype,shared))
    conn.commit()
    conn.close()
    return redirect("/files")