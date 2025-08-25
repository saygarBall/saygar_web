from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from lib.database2 import get_db, get_user
from werkzeug.utils import secure_filename
import os
import sqlite3  # นำเข้า sqlite3
from lib.utils import allowed_file  # Import ฟังก์ชันจาก utils
from functools import wraps

# ฟังก์ชันตรวจสอบสิทธิ์ผู้ใช้
def check_user_permission(required_rank):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if 'user_id' not in session:
                flash("คุณต้องเข้าสู่ระบบก่อน")
                return redirect(url_for('login'))
            user = get_user(session['user_id'])
            if user and user['rank'] == required_rank:
                return func(*args, **kwargs)
            flash("คุณไม่มีสิทธิเข้าถึงหน้านี้")
            return redirect(url_for('home.home'))
        return decorated_view
    return wrapper


# กำหนดโฟลเดอร์สำหรับอัปโหลดรูปภาพ
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ตรวจสอบว่าโฟลเดอร์อัปโหลดมีอยู่หรือไม่ ถ้าไม่มีก็สร้างขึ้น
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ฟังก์ชันสำหรับบันทึกไฟล์รูปภาพ
def save_profile_picture(profile_picture, email):
    if profile_picture and allowed_file(profile_picture.filename):
        file_extension = profile_picture.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{email.replace('@', '_')}.{file_extension}")
        filepath = os.path.join('static/uploads', filename)
        profile_picture.save(filepath)
        return filename
    else:
        flash('ไฟล์รูปโปรไฟล์ไม่รองรับ ควรเป็นไฟล์ประเภท png, jpg, jpeg หรือ gif')
        return None

# ฟังก์ชันลงทะเบียนผู้ใช้
def register_user(form_data, profile_picture):
    firstname = form_data['firstname']
    lastname = form_data['lastname']
    email = form_data['email']
    password = generate_password_hash(form_data['password'])
    phone = form_data['phone']  # เบอร์โทรศัพท์
    address_permanent = form_data['address_permanent']  # ที่อยู่ถาวร
    address_current = form_data['address_current']  # ที่อยู่ปัจจุบัน
    dob = form_data['dob']  # วันเดือนปีเกิด

    # บันทึกไฟล์รูปภาพโดยใช้ชื่อไฟล์เป็นอีเมล
    profile_filename = save_profile_picture(profile_picture, email)

    db = get_db()
    try:
        # ฟิลด์ registered_date จะใช้ค่า DEFAULT CURRENT_TIMESTAMP โดยอัตโนมัติ
        db.execute(
            '''
            INSERT INTO users (firstname, lastname, email, password, phone, address_permanent, address_current, dob, profile_picture) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (firstname, lastname, email, password, phone, address_permanent, address_current, dob, profile_filename)
        )
        db.commit()

        # เก็บ user_id ลงใน session
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        session['user_id'] = user['id']
    except sqlite3.IntegrityError:
        flash('อีเมลนี้มีการใช้งานแล้ว')

# ฟังก์ชันสำหรับตรวจสอบข้อมูลผู้ใช้
def authenticate_user(email, password):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        return True
    else:
        flash('อีเมลหรือรหัสผ่านไม่ถูกต้อง')
        return False
