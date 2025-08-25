import sqlite3

conn = sqlite3.connect('blind_service.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS post_likes (
        user_id INTEGER,
        post_title TEXT,
        service_id INTEGER,
        is_like INTEGER,
        PRIMARY KEY (user_id, post_title, service_id)
    )
''')

conn.commit()
conn.close()

print("✅ สร้างตาราง post_likes เรียบร้อยแล้ว")
