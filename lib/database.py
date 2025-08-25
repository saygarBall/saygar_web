import sqlite3
import os
from datetime import datetime
from docx import Document

DB_FILE = "database.db"
DATA_DIR = "data_base"
LOG_FILE = "log.txt"
BATCH_SIZE = 10  # Commit ทุก 10 ไฟล์
VALID_EXTENSIONS = [".txt", ".docx", ".mp3", ".wav", ".ogg", ".mp4", ".mov"]

def log_message(message):
    """ ฟังก์ชันบันทึกข้อความลง log.txt """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] {message}\n")

def get_db_connection():
    """ เชื่อมต่อฐานข้อมูล SQLite """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        log_message(f"Database error: {e}")
        return None

def ensure_tables_exist():
    """ สร้างตารางถ้ายังไม่มี """
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            path TEXT,
            parent_id INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            category_id INTEGER,
            updated_at TEXT,
            UNIQUE(title, category_id)
        )
    """)
    conn.commit()
    conn.close()

def cleanup_deleted_files():
    """ ลบบทความออกจากฐานข้อมูลถ้าไฟล์ถูกลบไปแล้ว และรีเซ็ต sequence """
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category_id FROM articles")
    articles = cursor.fetchall()
    deleted_articles = []
    for article_id, title, category_id in articles:
        cursor.execute("SELECT path FROM categories WHERE id=?", (category_id,))
        category_path_result = cursor.fetchone()
        if category_path_result:
            category_path = category_path_result["path"]
            file_exists = any(
                os.path.exists(os.path.join(category_path, f"{title}{ext}")) for ext in VALID_EXTENSIONS
            )
            if not file_exists:
                log_message(f"🛑 ลบจาก SQL เพราะหาไฟล์ไม่เจอ: {title} (ID: {article_id})")
                deleted_articles.append((article_id,))
    if deleted_articles:
        cursor.executemany("DELETE FROM articles WHERE id=?", deleted_articles)
        conn.commit()
        cursor.execute("UPDATE sqlite_sequence SET seq = (SELECT COUNT(*) FROM articles) WHERE name = 'articles'")
        conn.commit()
    conn.close()

def cleanup_deleted_categories():
    """ ลบหมวดหมู่ที่ไม่มีโฟลเดอร์อยู่แล้วออกจากฐานข้อมูล และรีเซ็ตจำนวน categories """
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()

    # ✅ ดึงข้อมูลหมวดหมู่ทั้งหมดจากฐานข้อมูล
    cursor.execute("SELECT id, name, path FROM categories")
    categories = cursor.fetchall()

    deleted_categories = []
    for category in categories:
        category_id, category_name, category_path = category

        # ✅ ตรวจสอบว่าโฟลเดอร์หมวดหมู่ยังมีอยู่หรือไม่
        if not os.path.exists(category_path):
            deleted_categories.append((category_id, category_name, category_path))

    if deleted_categories:
        print(f"🔴 กำลังลบหมวดหมู่ที่ไม่มีโฟลเดอร์อยู่แล้วทั้งหมด {len(deleted_categories)} รายการ...")

        for category_id, category_name, category_path in deleted_categories:
            print(f"🗑️ ลบหมวดหมู่จาก SQL: {category_name} (Path: {category_path})")

            # ✅ ลบ `articles` ที่อยู่ในหมวดหมู่นี้ก่อน
            cursor.execute("DELETE FROM articles WHERE category_id=?", (category_id,))

            # ✅ ลบ `subcategories` ที่อยู่ในหมวดหมู่นี้
            cursor.execute("DELETE FROM categories WHERE parent_id=?", (category_id,))

            # ✅ ลบ `categories` เอง
            cursor.execute("DELETE FROM categories WHERE id=?", (category_id,))
            conn.commit()

            log_message(f"🗑️ ลบหมวดหมู่ที่ไม่มีโฟลเดอร์แล้ว: {category_name}")

        # ✅ รีเซ็ต `sqlite_sequence` ของ `categories`
        cursor.execute("UPDATE sqlite_sequence SET seq = (SELECT COUNT(*) FROM categories) WHERE name = 'categories'")
        conn.commit()

    # ✅ ตรวจสอบจำนวนหมวดหมู่หลังลบ
    cursor.execute("SELECT COUNT(*) FROM categories")
    count_final = cursor.fetchone()[0]
    print(f"✅ จำนวนหมวดหมู่ที่เหลืออยู่: {count_final}")
    log_message(f"✅ จำนวนหมวดหมู่ที่เหลืออยู่: {count_final}")

    conn.close()

def load_data():
    """ โหลดข้อมูลจากโฟลเดอร์เข้าสู่ฐานข้อมูล """
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    for category in os.listdir(DATA_DIR):
        category_path = os.path.join(DATA_DIR, category)
        if not os.path.isdir(category_path):
            continue
        cursor.execute("SELECT id FROM categories WHERE name=?", (category,))
        result = cursor.fetchone()
        category_id = result["id"] if result else None
        if category_id is None:
            cursor.execute("INSERT INTO categories (name, path, parent_id) VALUES (?, ?, ?)",
                           (category, category_path, None))
            category_id = cursor.lastrowid
        for subcategory in os.listdir(category_path):
            subcategory_path = os.path.join(category_path, subcategory)
            if not os.path.isdir(subcategory_path):
                continue
            cursor.execute("SELECT id FROM categories WHERE name=? AND parent_id=?", (subcategory, category_id))
            result = cursor.fetchone()
            subcategory_id = result["id"] if result else None
            if subcategory_id is None:
                cursor.execute("INSERT INTO categories (name, path, parent_id) VALUES (?, ?, ?)",
                               (subcategory, subcategory_path, category_id))
                subcategory_id = cursor.lastrowid
            for file in os.listdir(subcategory_path):
                ext = os.path.splitext(file)[-1].lower()
                if ext not in VALID_EXTENSIONS:
                    continue
                file_path = os.path.join(subcategory_path, file)
                title = os.path.splitext(file)[0]
                file_mtime = int(os.path.getmtime(file_path))
                if ext == ".docx":
                    doc = Document(file_path)
                    content = "\n".join([p.text for p in doc.paragraphs])
                elif ext in [".mp3", ".wav", ".ogg", ".mp4", ".mov"]:
                    content = f"media_file={file}"
                else:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                cursor.execute("SELECT id FROM articles WHERE title=? AND category_id=?", (title, subcategory_id))
                existing_article = cursor.fetchone()
                if existing_article:
                    cursor.execute("UPDATE articles SET content=?, updated_at=? WHERE id=?",
                                   (content, file_mtime, existing_article["id"]))
                else:
                    cursor.execute("INSERT INTO articles (title, content, category_id, updated_at) VALUES (?, ?, ?, ?)",
                                   (title, content, subcategory_id, file_mtime))
    conn.commit()
    conn.close()

# ✅ ตรวจสอบและสร้างตารางหากยังไม่มี
ensure_tables_exist()
# ✅ โหลดข้อมูลก่อน เพื่อให้แน่ใจว่าทุกอย่างอยู่ในฐานข้อมูล
load_data()
# ✅ จากนั้นค่อยทำความสะอาดบทความที่ไม่มีไฟล์แล้ว
cleanup_deleted_files()
# ✅ ลบหมวดหมู่ที่ไม่มีโฟลเดอร์แล้วออกจากฐานข้อมูล
cleanup_deleted_categories()
