# lib/posts.py
import os
from datetime import datetime
from flask import flash
from lib.database2 import get_user
from lib.service_centers import get_service_name, get_all_service_centers
from lib.utils import allowed_file, create_folder_if_not_exists  # ปรับการนำเข้า allowed_file และ create_folder_if_not_exists

# สร้างโฟลเดอร์ตาม ID ศูนย์บริการและอีเมลของผู้ใช้
def create_service_folder(service_id, email=None):
    service_name = get_service_name(service_id)  
    folder_path = os.path.join('txt', service_name, email) if email else os.path.join('txt', service_name)
    create_folder_if_not_exists(folder_path)
    return folder_path

def handle_post(service_id, title, content, saved_images, firstname, lastname, user_rank, email):
    folder_path = create_service_folder(service_id, email)
    post_filepath = os.path.join(folder_path, f"{title}.txt")
    cleaned_content = content.strip().replace("\r\n", "\n")
    
    with open(post_filepath, 'w', encoding='utf-8') as f:
        f.write(f"โพสต์โดย: {firstname} {lastname} ({user_rank})\n")
        f.write(f"เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]}\n\n")
        if saved_images:
            f.write("รูปภาพที่แนบมา:\n")
            for image_name in saved_images:
                f.write(f"- {image_name}\n")
        f.write("รายละเอียด:\n")
        f.write(cleaned_content)
# ดึงข้อมูลโพสต์ทั้งหมดของศูนย์บริการ
def get_posts(service_id):
    folder_path = create_service_folder(service_id)
    posts = []
    if not os.path.exists(folder_path):
        return posts

    for user_email in os.listdir(folder_path):
        user_folder_path = os.path.join(folder_path, user_email)
        if os.path.isdir(user_folder_path):
            for filename in os.listdir(user_folder_path):
                if filename.endswith('.txt') and not filename.endswith('_comment.txt'):
                    file_path = os.path.join(user_folder_path, filename)
                    content = read_post_content(file_path)
                    user = get_user(user_email, by_email=True)
                    
                    posts.append({
                        'title': filename[:-4],
                        'content': content,
                        'author': f"{user['firstname']} {user['lastname']}" if user else "Unknown",
                        'rank': user['rank'] if user else "Unknown",
                        'profile_picture': user['profile_picture'] if user else 'default_profile.png',
                        'date': os.path.getmtime(file_path)
                    })
    return sorted(posts, key=lambda x: x['date'], reverse=True)

# อ่านเนื้อหาโพสต์ และดึงเฉพาะ 5 บรรทัดแรก
def read_post_content(file_path, limit_lines=False):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
    post_time = lines[1].strip() if len(lines) > 1 else "ไม่ทราบเวลา"
    content = "".join(lines)
    details_index = content.find("รายละเอียด:")
    
    if details_index != -1:
        content = content[details_index + len("รายละเอียด:"):].strip()
    
    content = f"เวลาโพสต์: {post_time}<br><br>{content}"
    
    # ดึง 5 บรรทัดแรกถ้าต้องการจำกัดบรรทัด
    return "<br>".join(content.split("<br>")[:5]) if limit_lines else content

# ดึงโพสต์ล่าสุดโดยจำกัดที่ 5 โพสต์แรก
def get_latest_posts():
    posts = []
    
    # Loop through all service centers (assuming service center folders exist)
    for service_id, service_name in get_all_service_centers().items():
        service_folder = create_service_folder(service_id)
        
        if not os.path.exists(service_folder):
            continue
        
        # Loop through all user folders
        for user_email in os.listdir(service_folder):
            user_folder = os.path.join(service_folder, user_email)
            
            if os.path.isdir(user_folder):
                # Loop through all post files in each user folder
                for filename in os.listdir(user_folder):
                    if filename.endswith('.txt') and not filename.endswith('_comment.txt'):
                        file_path = os.path.join(user_folder, filename)
                        content = read_post_content(file_path)
                        
                        # ดึงแค่ 5 บรรทัดแรกของเนื้อหา
                        first_5_lines = "<br>".join(content.splitlines()[:5])
                        
                        # เพิ่มรายละเอียดโพสต์เข้าไปในรายการ posts
                        posts.append({
                            'title': filename[:-4],  # ลบส่วนขยาย .txt สำหรับชื่อเรื่อง
                            'content': first_5_lines,  # แสดงเฉพาะ 5 บรรทัดแรก
                            'file_path': file_path,  # ใช้ในการเชื่อมโยงไปยังรายละเอียดโพสต์
                            'service_id': service_id,
                        })
    
    # เรียงโพสต์ตามวันที่ และแสดงโพสต์ล่าสุด 5 รายการ
    sorted_posts = sorted(posts, key=lambda x: os.path.getmtime(x['file_path']), reverse=True)[:5]
    
    return sorted_posts

def get_post_images(post_id):
    post_folder = os.path.join('static', 'uploads', str(post_id))
    return [
        filename for filename in os.listdir(post_folder) if allowed_file(filename)
    ] if os.path.exists(post_folder) else []