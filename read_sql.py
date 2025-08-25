import sqlite3
import csv

# กำหนดชื่อไฟล์ฐานข้อมูล SQL
database_file = 'blind_service.db'

# กำหนดชื่อไฟล์ txt ที่ต้องการสร้าง
output_file = 'output.txt'

# เชื่อมต่อฐานข้อมูล
conn = sqlite3.connect(database_file)
cursor = conn.cursor()

# ดึงชื่อตารางทั้งหมดในฐานข้อมูล
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

# เก็บข้อมูลจากทุกตาราง
all_data = []
for table in tables:
    table_name = table[0]
    cursor.execute(f'SELECT * FROM {table_name}')
    data = cursor.fetchall()
    all_data.extend(data)

# ปิดการเชื่อมต่อฐานข้อมูล
cursor.close()
conn.close()

# เขียนข้อมูลลงในไฟล์ txt
with open(output_file, 'w') as f:
    writer = csv.writer(f, delimiter='\t')  # ใช้ตัวแบ่งแท็บ (\t) ในการเขียนข้อมูล
    writer.writerows(all_data)

print(f'เขียนข้อมูลลงในไฟล์ {output_file} เรียบร้อยแล้ว')
