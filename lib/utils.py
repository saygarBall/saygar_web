#lib.utiles.py
import os
from flask import session, flash, redirect, url_for
from werkzeug.utils import secure_filename
from lib.database2 import get_user

def get_greeting():
    if 'user_id' in session and session.get('user_id'):  
        user = get_user(session['user_id'])
        if user:
            rank = user['rank']
            first_name, last_name = user['firstname'], user['lastname']
            if rank == 'user_default':
                return f"ยินดีต้อนรับคุณ {first_name} {last_name} (User default)"
            elif rank == 'user_admin':
                return f"ยินดีต้อนรับคุณ {first_name} {last_name} (User admin)"
            elif rank == 'user_administrator_and_manage_systems':
                return f"ยินดีต้อนรับคุณ {first_name} {last_name} (System Manager)"
    return "คุณยังไม่ได้เป็นสมาชิก"


def check_user_rank(user_rank, required_rank):
    if user_rank != required_rank:
        flash('คุณไม่มีสิทธิเข้าถึงหน้านี้')
        return redirect(url_for('index'))
    return None

def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image, folder):
    filename = secure_filename(image.filename)
    filepath = os.path.join(folder, filename)
    image.save(filepath)
    return filename

def sanitize_filename(name):
    import re
    return re.sub(r'[\\/:"*?<>|]+', "", name).strip()
