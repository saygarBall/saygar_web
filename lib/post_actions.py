# lib/post_actions.py
import os
from datetime import datetime
from flask import redirect, url_for, flash
from lib.database2 import get_user  # ใช้ get_user แทน get_user_by_email
from lib.service_centers import get_service_name  # Import service name function
from flask import session, request, jsonify
from lib.database2 import get_db

# Function to log actions into log.txt
def log_action(action, details=""):
    with open('log.txt', 'a', encoding='utf-8') as log_file:
        log_file.write(f"{datetime.now()} - {action}: {details}\n")

# Check if the user is the post owner
def check_post_owner(service_id, post_title, email):
    if email is None:
        log_action("Email not provided", "Failed to check post ownership")
        return False

    service_name = get_service_name(service_id)  # Get service name using the centralized function
    post_folder = os.path.join('txt', service_name, email)
    post_filepath = os.path.join(post_folder, f"{post_title}.txt")
    return os.path.exists(post_filepath)

# Save comments to a file
def save_comment(service_id, post_title, comment_content, firstname, lastname, user_email, post_owner_email):
    service_name = get_service_name(service_id)
    post_folder = os.path.join('txt', service_name, post_owner_email)
    
    if not os.path.exists(post_folder):
        os.makedirs(post_folder)

    comment_filename = f"{post_title}_comment.txt"
    comment_filepath = os.path.join(post_folder, comment_filename)

    comment_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]

    # Save the comment with email for easy profile picture lookup
    with open(comment_filepath, 'a', encoding='utf-8') as f:
        f.write(f"{firstname} {lastname} ({user_email}):{comment_content}:{comment_time}\n")

# Fetch the post content and associated comments
def get_post_and_comments(service_id, post_title, post_owner_email):
    service_name = get_service_name(service_id)
    post_folder = os.path.join('txt', service_name, post_owner_email)

    if not os.path.exists(post_folder):
        return "ไม่พบโพสต์", []

    post_filepath = os.path.join(post_folder, f"{post_title}.txt")
    if not os.path.exists(post_filepath):
        return "ไม่พบโพสต์", []

    post_content = read_post_content(post_filepath)
    comments = []
    comment_filepath = os.path.join(post_folder, f"{post_title}_comment.txt")

    if os.path.exists(comment_filepath):
        with open(comment_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                parsed = line.strip().split(':', 2)
                if len(parsed) == 3:
                    author_info, content, timestamp = parsed
                    # ดึง user_id ที่เป็นตัวเลขจากอีเมล
                    email = author_info.split("(")[-1].strip(")")
                    user = get_user(email, by_email=True)
                    if user:
                        profile_picture = user['profile_picture']
                        user_id = user['id']
                    else:
                        profile_picture = 'default_profile.png'
                        user_id = None
                    
                    comments.append({
                        'author': author_info,
                        'content': content,
                        'user_id': user_id,  # ใช้ user_id ที่เป็นตัวเลข
                        'time': timestamp,
                        'profile_picture': profile_picture
                    })

    return post_content, comments

def read_post_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    content = "".join(lines)
    details_index = content.find("รายละเอียด:")
    if details_index != -1:
        content = content[details_index + len("รายละเอียด:"):].strip()

    return content

def get_post_owner_email(service_id, post_title):
    service_name = get_service_name(service_id)
    service_folder = os.path.join('txt', service_name)

    for user_email in os.listdir(service_folder):
        user_folder = os.path.join(service_folder, user_email)
        if os.path.isdir(user_folder):
            post_filepath = os.path.join(user_folder, f"{post_title}.txt")
            if os.path.exists(post_filepath):
                log_action("Post owner found", f"Owner: {user_email}")
                return user_email

    log_action("Post owner not found", f"Service ID: {service_id}, Post Title: {post_title}")
    return None

# Function to delete a comment
def delete_comment(service_id, post_title, comment_author, comment_time, user_email):
    service_name = get_service_name(service_id)
    comment_filepath = os.path.join('txt', service_name, user_email, f"{post_title}_comment.txt")

    if not os.path.exists(comment_filepath):
        log_action("Comment file not found", comment_filepath)
        return False

    updated_comments = []
    with open(comment_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            parsed = line.strip().split(":", 2)
            if len(parsed) == 3 and (parsed[0] != comment_author or parsed[2] != comment_time):
                updated_comments.append(line)

    with open(comment_filepath, 'w', encoding='utf-8') as f:
        f.writelines(updated_comments)

    log_action("Comment deleted", f"Service ID: {service_id}, Post Title: {post_title}, Author: {comment_author}, Comment Time: {comment_time}")
    return True

# Function to edit a comment
def edit_comment(service_id, post_title, comment_author, comment_time, new_content, user_email):
    service_name = get_service_name(service_id)
    comment_filepath = os.path.join('txt', service_name, user_email, f"{post_title}_comment.txt")

    if not os.path.exists(comment_filepath):
        log_action("Comment file not found", comment_filepath)
        return False

    updated_comments = []
    with open(comment_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            parsed = line.strip().split(":", 2)
            if len(parsed) == 3 and parsed[0] == comment_author and parsed[2] == comment_time:
                updated_comments.append(f"{parsed[0]}:{new_content}:{parsed[2]}\n")
            else:
                updated_comments.append(line)

    with open(comment_filepath, 'w', encoding='utf-8') as f:
        f.writelines(updated_comments)

    log_action("Comment edited", f"Service ID: {service_id}, Post Title: {post_title}, Author: {comment_author}, Comment Time: {comment_time}")
    return True

from flask import jsonify

def like_post():
    if 'user_id' not in session:
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 403

    user_id = session['user_id']
    data = request.json
    post_title = data['post_title']
    service_id = data['service_id']
    is_like = data['is_like']

    with get_db() as conn:  # Using context manager for the connection
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO post_likes (user_id, post_title, service_id, is_like)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, post_title, service_id)
            DO UPDATE SET is_like=excluded.is_like
        """, (user_id, post_title, service_id, is_like))
        conn.commit()

        # Get the latest like/dislike count
        like_count = cursor.execute("SELECT COUNT(*) FROM post_likes WHERE post_title=? AND service_id=? AND is_like=1", (post_title, service_id)).fetchone()[0]
        dislike_count = cursor.execute("SELECT COUNT(*) FROM post_likes WHERE post_title=? AND service_id=? AND is_like=0", (post_title, service_id)).fetchone()[0]

    return jsonify({'likes': like_count, 'dislikes': dislike_count})

def get_post_like_counts(service_id, post_title):
    conn = get_db()
    cursor = conn.cursor()
    likes = cursor.execute("SELECT COUNT(*) FROM post_likes WHERE post_title=? AND service_id=? AND is_like=1", (post_title, service_id)).fetchone()[0]
    dislikes = cursor.execute("SELECT COUNT(*) FROM post_likes WHERE post_title=? AND service_id=? AND is_like=0", (post_title, service_id)).fetchone()[0]
    # ❌ อย่า close db ที่นี่
    return likes, dislikes
