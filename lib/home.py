from flask import Blueprint, render_template, session
import sqlite3
from lib.database import DB_FILE
import os
from lib.utils import get_greeting
from lib.auth import get_user

home_bp = Blueprint("home", __name__)
TITLE_FOLDER = "title"

@home_bp.route("/")
def home():
    """ โหลดหมวดหมู่หลักและหมวดหมู่ย่อยจากฐานข้อมูล """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # ✅ ดึงหมวดหมู่หลัก และตัด "h_" ออก
    cursor.execute("SELECT id, name FROM categories WHERE parent_id IS NULL")
    categories = {id: {"name": name[2:] if name.startswith("h_") else name, "subcategories": []} for id, name in cursor.fetchall()}

    # ✅ ดึงหมวดหมู่ย่อย และเพิ่มเข้าไปใน `categories`
    cursor.execute("SELECT id, name, parent_id FROM categories WHERE parent_id IS NOT NULL")
    for sub_id, sub_name, parent_id in cursor.fetchall():
        if parent_id in categories:
            categories[parent_id]["subcategories"].append((sub_id, sub_name))

    # ✅ ดึงบทความล่าสุด
    cursor.execute("SELECT id, title FROM articles ORDER BY updated_at DESC LIMIT 5")
    latest_articles = cursor.fetchall()

    conn.close()

    # อ่านไฟล์ในโฟลเดอร์ 'title'
    title_contents = []
    if os.path.exists(TITLE_FOLDER):
        for filename in os.listdir(TITLE_FOLDER):
            if filename.endswith(".txt"):
                filepath = os.path.join(TITLE_FOLDER, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip().replace("\n", "<br>")
                    heading = os.path.splitext(filename)[0]
                    title_contents.append({"heading": heading, "content": content})

    greeting = get_greeting()  # ✅ เรียกใช้ฟังก์ชัน
    user_id = session.get("user_id")
    user = get_user(user_id) if user_id else None

    return render_template(
        "index.html",
        greeting=greeting,
        user=user,
        categories=categories.items(),
        latest_articles=latest_articles,
        title_contents=title_contents
    )