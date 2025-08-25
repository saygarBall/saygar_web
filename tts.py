import os
import sqlite3
from gtts import gTTS
import re
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")

def sanitize_filename(name):
    """ ลบอักขระที่ไม่ปลอดภัยออกจากชื่อไฟล์ """
    return re.sub(r'[\\/:"*?<>|]+', "", name).strip()

def ensure_audio_dir():
    os.makedirs(AUDIO_DIR, exist_ok=True)

def should_skip_content(content):
    """ ข้ามบทความที่มี download_file= หรือ media_file= """
    lines = content.lower().splitlines()
    return any(line.startswith("download_file=") or line.startswith("media_file=") for line in lines)

def generate_tts(title, content):
    """ สร้างเสียงจากบทความ """
    try:
        clean_title = sanitize_filename(title)
        output_path = os.path.join(AUDIO_DIR, f"{clean_title}.mp3")

        if os.path.exists(output_path):
            print(f"✅ ข้าม: {clean_title}.mp3 (มีอยู่แล้ว)")
            return

        if should_skip_content(content):
            print(f"⚠ ข้าม: {clean_title} (มี download_file= หรือ media_file=)")
            return

        print(f"🎤 สร้างเสียง: {clean_title}.mp3 ...")
        tts = gTTS(text=content, lang="th")
        tts.save(output_path)
        print(f"✅ เสร็จแล้ว -> {output_path}")
    except Exception as e:
        print(f"❌ ผิดพลาดที่: {title} → {e}")

def process_articles():
    ensure_audio_dir()

    if not os.path.exists(DB_FILE):
        print(f"❌ ไม่พบไฟล์ฐานข้อมูล: {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM articles")
    articles = cursor.fetchall()
    conn.close()

    print(f"🔎 ตรวจสอบบทความทั้งหมด: {len(articles)} รายการ")

    with ThreadPoolExecutor(max_workers=5) as executor:
        for title, content in articles:
            if not title or not content.strip():
                continue
            executor.submit(generate_tts, title, content)

if __name__ == "__main__":
    print("🚀 เริ่มแปลงบทความเป็นเสียง (ข้ามบทความที่มี download/media หรือมี mp3 อยู่แล้ว)...")
    process_articles()
    print("🎉 เสร็จสมบูรณ์ทุกไฟล์แล้วครับ!")
