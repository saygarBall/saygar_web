# lib/database.py
import sqlite3
from flask import g

# กำหนดชื่อไฟล์ฐานข้อมูล
DATABASE = 'blind_service.db'

# ฟังก์ชันสำหรับเชื่อมต่อฐานข้อมูล
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

# ฟังก์ชันปิดการเชื่อมต่อฐานข้อมูล
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ฟังก์ชันสำหรับสร้างตารางต่าง ๆ ตอนเริ่มต้นแอพ
def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # ตาราง users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone TEXT NOT NULL,
                address_permanent TEXT NOT NULL,
                address_current TEXT NOT NULL,
                dob DATE,
                profile_picture TEXT,
                rank TEXT NOT NULL DEFAULT 'user_default',
                registered_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ตาราง post_likes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_likes (
                user_id INTEGER NOT NULL,
                post_title TEXT NOT NULL,
                service_id INTEGER NOT NULL,
                is_like INTEGER NOT NULL,
                PRIMARY KEY (user_id, post_title, service_id)
            )
        ''')

        # เพิ่มดัชนี (Index) เพื่อการค้นหาที่เร็วขึ้น
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON users (email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON users (id);")

        db.commit()

# ฟังก์ชันอัปเดต rank ของผู้ใช้ด้วย user_id
def update_user_rank(user_id, new_rank):
    db = get_db()
    db.execute("UPDATE users SET rank = ? WHERE id = ?", (new_rank, user_id))
    db.commit()

# ฟังก์ชันอัปเดต rank ของผู้ใช้ด้วย email
def update_user_rank_by_email(email, new_rank):
    user = get_user(email, by_email=True)
    if user:
        update_user_rank(user['id'], new_rank)
        return True
    return False

# ฟังก์ชันดึงข้อมูลผู้ใช้
def get_user(identifier, by_email=False):
    db = get_db()
    cursor = db.cursor()
    if by_email:
        cursor.execute("SELECT * FROM users WHERE email = ?", (identifier,))
    else:
        cursor.execute("SELECT * FROM users WHERE id = ?", (identifier,))
    return cursor.fetchone()

# ฟังก์ชันเรียกตอนเริ่มต้นเพื่อ setup database และตั้งค่า admin
def setup_app(app):
    with app.app_context():
        init_db(app)
        # ตั้งค่าผู้ใช้ email นี้เป็น user_administrator_and_manage_systems ทันที
        update_user_rank_by_email('arkarachaiwww123@gmail.com', 'user_administrator_and_manage_systems')
