from db import db
from flask import session
from sqlalchemy.sql import text
from werkzeug.security import check_password_hash, generate_password_hash

def login(username, password):
    sql = text("SELECT id, password FROM users WHERE username = :username")
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()

    if not user:
        return False

    if check_password_hash(user.password, password):
        user_id = user.id
        session["username"] = username
        session["id"] = user_id
        return True
    
    return False

def logout():
    del session["username"]
    del session["id"]

def register(username, password, data):
    sql = text("SELECT id FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    if user:
        return False
    hash_value = generate_password_hash(password)
    sql = text("INSERT INTO users (username, password, data) VALUES (:username, :password, :data) RETURNING id")
    result = db.session.execute(sql, {"username": username, "password": hash_value, "data": data})
    user_id = result.fetchone()[0]
    db.session.commit()
    session["username"] = username
    session["id"] = user_id
    return True

def delete_account(id):
    sql = text("DELETE FROM users WHERE id = :id")
    db.session.execute(sql, {"id": id})
    del session["username"]
    del session["id"]
    db.session.commit()

def change_pfp(file):
    user_id = session["id"]
    sql = text("UPDATE users SET data = :data WHERE id = :user_id")
    db.session.execute(sql, {"data": file, "user_id": user_id})
    db.session.commit()