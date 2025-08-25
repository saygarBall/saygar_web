import os

def copy_file_contents():
    # ใช้ os.getcwd() เพื่อดึงพาธของโฟลเดอร์ที่รันโปรแกรม
    folder_path = os.getcwd()
    
    # เปิดไฟล์ x.txt เพื่อบันทึกผลลัพธ์
    with open('x.txt', 'w', encoding='utf-8') as output_file:
        # วนลูปเพื่ออ่านไฟล์ทั้งหมดในโฟลเดอร์และโฟลเดอร์ย่อย
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # ยกเว้นไฟล์ชื่อ copy.py และ x.txt
                if file == 'copy.py' or file == 'x.txt':
                    continue
                
                # เช็คเฉพาะไฟล์ที่มีนามสกุล .txt และ .py
                if file.endswith('.txt') or file.endswith('.py') or file.endswith('.html'):
                    # สร้างชื่อไฟล์เต็ม
                    file_path = os.path.join(root, file)
                    # หากไฟล์อยู่ในโฟลเดอร์ย่อย จะสร้างชื่อให้ชัดเจน
                    file_name = file_path.replace(folder_path + os.sep, '').replace(os.sep, '.')
                    
                    # เขียนชื่อไฟล์ลงในไฟล์ x.txt
                    output_file.write(f"#{file_name}\n")
                    
                    # อ่านเนื้อหาไฟล์และบันทึกลงในไฟล์ x.txt
                    with open(file_path, 'r', encoding='utf-8') as f:
                        output_file.write(f.read())
                        output_file.write("\n")  # เพิ่มบรรทัดว่างหลังจบเนื้อหาไฟล์

# เรียกใช้งานฟังก์ชัน
copy_file_contents()
