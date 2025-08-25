# lib/service_centers.py
SERVICE_CENTERS = {
    1: 'สร้างกระทู้เพื่อสอบถามข้อมูลหรือพูดคุย',
    2: 'สร้างกระทู้เพื่อขอความช่วยเหลือ'
}

def get_all_service_centers():
    # Return all service centers
    return SERVICE_CENTERS

def get_service_name(service_id):
    # Return the name of a specific service center by its ID
    return SERVICE_CENTERS.get(service_id, f"ศูนย์บริการ {service_id}")

import os

def get_service_intro(service_name):
    # สร้าง path ของไฟล์แนะนำศูนย์บริการ
    filename = f"title_{service_name}.txt"
    file_path = os.path.join('txt', service_name, filename)

    # ตรวจสอบว่าไฟล์มีอยู่หรือไม่ ถ้ามีให้เปิดอ่านและส่งข้อมูลกลับไป
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()  # ส่งข้อความในไฟล์กลับไป (ลบช่องว่างและบรรทัดว่าง)
    else:
        # ถ้าไม่พบไฟล์ ให้ส่งข้อความเริ่มต้นกลับไป
        return "ยินดีต้อนรับ"

