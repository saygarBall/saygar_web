from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from werkzeug.utils import secure_filename
import os
from lib.database2 import get_db  # นำเข้า get_db จาก database.py เพื่อหลีกเลี่ยง circular import
from lib.utils import allowed_file  # Import ฟังก์ชันจาก utils

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

account_blueprint = Blueprint('account', __name__)

# ตรวจสอบและสร้างโฟลเดอร์อัปโหลดหากยังไม่มี
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Route สำหรับหน้า บัญชีของฉัน
@account_blueprint.route('/account', methods=['GET'])
def account():
    if 'user_id' in session:
        user_id = session['user_id']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return render_template('account.html', user=user)
    return redirect(url_for('auth.login'))

# Route สำหรับการแก้ไขข้อมูลส่วนตัว
@account_blueprint.route('/account/edit', methods=['GET', 'POST'])
def edit_account():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        phone = request.form['phone']
        address_permanent = request.form['address_permanent']
        address_current = request.form['address_current']
        dob = request.form['dob']

        # ตรวจสอบไฟล์รูปโปรไฟล์
        profile_picture = request.files['profile_picture']
        if profile_picture and allowed_file(profile_picture.filename):
            # กำหนดชื่อไฟล์ตามอีเมลและบันทึกไฟล์ใหม่
            filename = secure_filename(email.replace('@', '_') + '.' + profile_picture.filename.rsplit('.', 1)[1].lower())
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            profile_picture.save(filepath)
        else:
            # ใช้รูปโปรไฟล์เดิมถ้าไม่มีการอัปโหลดไฟล์ใหม่
            filename = user['profile_picture']

        # อัปเดตข้อมูลอื่นๆ
        db.execute('''
            UPDATE users SET firstname = ?, lastname = ?, email = ?, phone = ?, address_permanent = ?, 
            address_current = ?, dob = ?, profile_picture = ? WHERE id = ?
        ''', (firstname, lastname, email, phone, address_permanent, address_current, dob, filename, user_id))
        db.commit()
        flash('ข้อมูลส่วนตัวถูกอัปเดตเรียบร้อยแล้ว')
        return redirect(url_for('account.account'))
    
    return render_template('edit_account.html', user=user)
