#lib.user_management.py
from flask import flash, session, redirect, url_for
from lib.database2 import get_db

def promote_user_to_admin(user_id):
    db = get_db()
    db.execute("UPDATE users SET rank = 'user_admin' WHERE id = ?", (user_id,))
    db.commit()
    flash('โปรโมตผู้ใช้เป็นผู้ดูแลระบบเรียบร้อยแล้ว')

def demote_user_to_default(user_id):
    db = get_db()
    db.execute("UPDATE users SET rank = 'user_default' WHERE id = ?", (user_id,))
    db.commit()
    flash('ลดระดับผู้ใช้เป็นผู้ใช้ทั่วไปเรียบร้อยแล้ว')

def get_user_details(user_id):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

def get_all_users():
    db = get_db()
    return db.execute("SELECT * FROM users").fetchall()
