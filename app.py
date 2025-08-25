#app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from lib.database import load_data, get_db_connection
from lib.home import home_bp
from lib.service import service_bp
from lib.content import content_bp
from lib.search import search_bp
import sqlite3
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from lib.posts import handle_post, get_posts, get_latest_posts, create_service_folder, get_post_images
from lib.database2 import get_db, init_db, setup_app, get_user, update_user_rank, update_user_rank_by_email
from lib.auth import register_user, authenticate_user
from lib.user_management import promote_user_to_admin, demote_user_to_default, get_all_users
from lib.post_actions import *
from lib.service_centers import get_service_name, get_all_service_centers, get_service_intro
from lib.accounts import account_blueprint
from lib.utils import allowed_file, check_user_rank, create_folder_if_not_exists, save_image, get_greeting, sanitize_filename
import os
from lib.auth import check_user_permission



app = Flask(__name__)
app.secret_key = 'arkarachaicojwlkasdic84ljJIJOfjwkja9c5553'
app.register_blueprint(account_blueprint)



app.register_blueprint(home_bp)
app.register_blueprint(service_bp)
app.register_blueprint(content_bp)
app.register_blueprint(search_bp)

@app.route('/index2')
def index2():
    greeting = get_greeting()
    user = get_user(session['user_id']) if 'user_id' in session else None
    
    service_centers = get_all_service_centers()
    latest_posts = get_latest_posts()

    # ใช้ get_post_images เพื่อดึงข้อมูลรูปภาพ
    post_images = {post['title']: get_post_images(post['title']) for post in latest_posts}

    return render_template('index2.html', greeting=greeting, user=user, service_centers=service_centers, latest_posts=latest_posts, post_images=post_images)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form_data = request.form
        profile_picture = request.files['profile_picture']
        register_user(form_data, profile_picture)
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/manage_users')
@check_user_permission('user_administrator_and_manage_systems')
def manage_users():
    users = get_all_users()
    return render_template('manage_users.html', users=users)

@app.route('/user_details/<int:id>', methods=['GET', 'POST'])
@check_user_permission('user_administrator_and_manage_systems')
def user_details(id):
    user = get_user(id)
    if request.method == 'POST':
        new_rank = request.form.get('rank')
        if new_rank in ['user_default', 'user_admin']:
            update_user_rank(id, new_rank)
            flash('การเปลี่ยนแปลงระดับผู้ใช้สำเร็จ')
            return redirect(url_for('manage_users'))
    return render_template('user_details.html', user=user)

@app.route('/change_user_rank/<int:id>', methods=['POST'])
def change_user_rank(id):
    if 'user_id' in session and session.get('user_id'):
        user_id = session['user_id']
        user = get_user(user_id)
        if user['rank'] == 'user_administrator_and_manage_systems':
            new_rank = request.form['rank']
            update_user_rank(id, new_rank)
            flash('บทบาทของผู้ใช้ได้ถูกเปลี่ยนแล้ว')
        else:
            flash('คุณไม่มีสิทธิเข้าถึงหน้านี้')
    else:
        flash('กรุณาเข้าสู่ระบบก่อน')
    return redirect(url_for('manage_users'))

@app.route('/account')
def account():
    user = get_user(session['user_id']) if 'user_id' in session else None
    return render_template('account.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            session.permanent = True
            return redirect(url_for('home.home'))
        else:
            flash('อีเมลหรือรหัสผ่านไม่ถูกต้อง')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # ลบข้อมูล session ทั้งหมด
    flash('คุณได้ออกจากระบบเรียบร้อยแล้ว')
    return redirect(url_for('home.home'))

@app.route('/promote_user/<int:id>')
def promote_user(id):
    if 'user_id' in session and session.get('user_id'):
        user_id = session['user_id']
        db = get_db()
        current_user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if current_user['rank'] == 'user_administrator_and_manage_systems':
            db.execute("UPDATE users SET rank = 'user_admin' WHERE id = ?", (id,))
            db.commit()
            flash('โปรโมตผู้ใช้เป็นผู้ดูแลระบบเรียบร้อยแล้ว')
            return redirect(url_for('manage_users'))
        else:
            flash('คุณไม่มีสิทธิเข้าถึงหน้านี้')
            return redirect(url_for('index2'))
    return redirect(url_for('login'))

@app.route('/demote_user/<int:id>')
@check_user_permission('user_administrator_and_manage_systems')
def demote_user(id):
    update_user_rank(id, 'user_default')
    flash('ลดระดับผู้ใช้เป็นผู้ใช้ทั่วไปเรียบร้อยแล้ว')
    return redirect(url_for('manage_users'))

@app.route('/post_service_center/<int:service_id>', methods=['GET', 'POST'])
def post_service_center(service_id):
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        images = request.files.getlist('image')

        post_folder = os.path.join(app.root_path, 'static', 'uploads', secure_filename(title))
        create_folder_if_not_exists(post_folder)

        saved_image_names = [save_image(image, post_folder) for image in images if image and allowed_file(image.filename)]

        # Check if user is logged in
        if 'user_id' in session and session.get('user_id'):
            user = get_user(session['user_id'])
            firstname, lastname, user_rank, email = user['firstname'], user['lastname'], user['rank'], user['email']
        else:
            flash("คุณต้องเข้าสู่ระบบก่อนถึงจะโพสต์ได้")
            return redirect(url_for('login'))

        handle_post(service_id, title, content, saved_image_names, firstname, lastname, user_rank, email)
        flash('โพสต์ถูกบันทึกเรียบร้อยแล้ว!')
        return redirect(url_for('service_center', service_id=service_id))

    flash('Method ไม่ถูกต้อง')
    return redirect(url_for('index2'))


@app.route('/post_actions/<int:service_id>/<post_title>', methods=['GET', 'POST'])
def post_actions(service_id, post_title):
    post_owner_email = get_post_owner_email(service_id, post_title)
    post_content, comments = get_post_and_comments(service_id, post_title, post_owner_email)
    like_count, dislike_count = get_post_like_counts(service_id, post_title)

    post_images = get_post_images(post_title)

    user = get_user(session['user_id']) if 'user_id' in session else None
    is_owner = user and user['email'] == post_owner_email

    # ✅ ป้องกัน profile_picture เป็น None
    post_owner = get_user(post_owner_email, by_email=True)
    if post_owner and post_owner['profile_picture']:
        post_owner_profile_picture = post_owner['profile_picture']
    else:
        post_owner_profile_picture = 'default_profile.png'

    if request.method == 'POST' and 'comment' in request.form:
        if user:
            comment_content = request.form['comment']
            save_comment(service_id, post_title, comment_content, user['firstname'], user['lastname'], user['email'], post_owner_email)
            flash('คอมเมนต์ถูกบันทึกแล้ว!')
        else:
            flash("คุณต้องเข้าสู่ระบบก่อนถึงจะแสดงความคิดเห็นได้")
        return redirect(request.url)

    return render_template(
        'post_actions.html', 
        post_title=post_title, 
        post_content=post_content, 
        comments=comments, 
        is_owner=is_owner,
        service_id=service_id, 
        user=user,
        post_owner_profile_picture=post_owner_profile_picture,
        post_images=post_images,
        like_count=like_count,
        dislike_count=dislike_count
    )

@app.route('/delete_post/<int:service_id>/<post_title>', methods=['POST'])
def delete_post(service_id, post_title):
    if 'user_id' in session and session.get('user_id'):
        user_id = session['user_id']
        user = get_user(user_id)
        if check_post_owner(service_id, post_title, user['email']):
            post_folder = create_service_folder(service_id, user['email'])
            post_filepath = os.path.join(post_folder, f"{post_title}.txt")

            if os.path.exists(post_filepath):
                os.remove(post_filepath)
                flash("โพสต์ถูกลบเรียบร้อยแล้ว")
            else:
                flash("ไม่พบไฟล์โพสต์ที่ต้องการลบ")

            return redirect(url_for('service_center', service_id=service_id))
        else:
            flash("คุณไม่มีสิทธิ์ในการลบโพสต์นี้")
    return redirect(url_for('service_center', service_id=service_id))

@app.route('/edit_post/<int:service_id>/<post_title>', methods=['GET', 'POST'])
def edit_post(service_id, post_title):
    if 'user_id' in session and session.get('user_id'):
        user_id = session['user_id']
        user = get_user(user_id)

        if check_post_owner(service_id, post_title, user['email']):
            post_folder = create_service_folder(service_id, user['email'])
            post_filepath = os.path.join(post_folder, f"{post_title}.txt")

            # อ่านเนื้อหาจากไฟล์ โดยไม่เพิ่ม newline เพิ่มเติม
            post_content = read_post_content(post_filepath).strip()

            if request.method == 'POST':
                new_content = request.form['new_content'].strip().replace("\r\n", "\n")  # จัดการ newline ในเนื้อหาใหม่
                
                # บันทึกเนื้อหาใหม่ลงไฟล์
                with open(post_filepath, 'w', encoding='utf-8') as f:
                    f.write(f"โพสต์โดย: {user['firstname']} {user['lastname']} ({user['rank']})\n")
                    f.write(f"เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]}\n\n")
                    f.write("รายละเอียด:\n")
                    f.write(new_content)  # บันทึกเนื้อหาใหม่ที่จัดการ newline

                flash("โพสต์ถูกแก้ไขเรียบร้อยแล้ว")
                return redirect(url_for('post_actions', service_id=service_id, post_title=post_title))

            return render_template('edit_post.html', post_title=post_title, post_content=post_content)
        else:
            flash("คุณไม่มีสิทธิ์ในการแก้ไขโพสต์นี้")
    return redirect(url_for('service_center', service_id=service_id))

@app.route('/edit_comment/<int:service_id>/<post_title>/<comment_time>', methods=['POST'])
def edit_comment(service_id, post_title, comment_time):
    if 'user_id' in session and session.get('user_id'):
        user_id = session['user_id']
        user = get_user(user_id)

        post_owner_email = get_post_owner_email(service_id, post_title)
        post_content, comments = get_post_and_comments(service_id, post_title, post_owner_email)

        new_content = request.form['new_content']

        comment_filepath = os.path.join('txt', get_service_name(service_id), post_owner_email, f"{post_title}_comment.txt")
        updated_comments = []
        
        with open(comment_filepath, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                parsed = line.strip().split(':', 2)
                if len(parsed) == 3 and parsed[2] == comment_time and parsed[0] == f"{user['firstname']} {user['lastname']}":
                    updated_comments.append(f"{parsed[0]}:{new_content}:{parsed[2]}\n")
                else:
                    updated_comments.append(line)

        with open(comment_filepath, 'w', encoding='utf-8') as f:
            f.writelines(updated_comments)

        flash('คอมเมนต์ถูกแก้ไขเรียบร้อยแล้ว')
        return redirect(url_for('post_actions', service_id=service_id, post_title=post_title))

    flash('คุณต้องเข้าสู่ระบบก่อนถึงจะแก้ไขคอมเมนต์ได้')
    return redirect(url_for('login'))

@app.route('/delete_comment/<int:service_id>/<post_title>/<comment_time>', methods=['POST'])
def delete_comment(service_id, post_title, comment_time):
    if 'user_id' in session and session.get('user_id'):
        user_id = session['user_id']
        user = get_user(user_id)

        post_owner_email = get_post_owner_email(service_id, post_title)
        comment_filepath = os.path.join('txt', get_service_name(service_id), post_owner_email, f"{post_title}_comment.txt")
        updated_comments = []

        with open(comment_filepath, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                parsed = line.strip().split(':', 2)
                if len(parsed) == 3 and parsed[2] == comment_time and parsed[0] == f"{user['firstname']} {user['lastname']}":
                    continue
                updated_comments.append(line)

        with open(comment_filepath, 'w', encoding='utf-8') as f:
            f.writelines(updated_comments)

        flash('คอมเมนต์ถูกลบเรียบร้อยแล้ว')
        return redirect(url_for('post_actions', service_id=service_id, post_title=post_title))

    flash('คุณต้องเข้าสู่ระบบก่อนถึงจะลบคอมเมนต์ได้')
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/service_center/<int:service_id>')
def service_center(service_id):
    service_name = get_service_name(service_id)
    posts = get_posts(service_id)
    greeting = get_greeting()

    # เรียกฟังก์ชันเพื่อดึงข้อมูลแนะนำของศูนย์บริการ
    service_intro = get_service_intro(service_name)

    # ดึงข้อมูลรูปภาพของโพสต์ทั้งหมด
    post_images = {}
    for post in posts:
        post_folder = os.path.join('static', 'uploads', post['title'])
        if os.path.exists(post_folder):
            post_images[post['title']] = [
                filename for filename in os.listdir(post_folder) if allowed_file(filename)
            ]
        else:
            post_images[post['title']] = []

    user = get_user(session['user_id']) if 'user_id' in session else None
    return render_template(
        'service_center.html', 
        posts=posts, 
        service_name=service_name, 
        service_id=service_id, 
        greeting=greeting, 
        user=user,
        post_images=post_images,  # ส่งข้อมูลรูปภาพไปยังเทมเพลต
        service_intro=service_intro  # ส่งข้อมูลแนะนำไปยังเทมเพลต
    )

@app.route("/admin-dashboard")
def admin_dashboard():
    query = request.args.get("q", "").strip()
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row

    if query:
        rows = conn.execute("SELECT id, title FROM articles WHERE title LIKE ?", (f"%{query}%",)).fetchall()
    else:
        rows = conn.execute("SELECT id, title FROM articles").fetchall()
    conn.close()

    # ดึง user จาก session เพื่อใช้ใน base.html
    user = get_user(session['user_id']) if 'user_id' in session else None

    articles = []
    for row in rows:
        filename = f"{sanitize_filename(row['title'])}.mp3"
        exists = os.path.exists(os.path.join("static", "audio", filename))
        articles.append({
            "id": row["id"],
            "title": row["title"],
            "tts_exists": exists
        })

    return render_template("admin_dashboard.html", articles=articles, user=user)

@app.route("/delete-article/<int:article_id>", methods=["POST"])
def delete_article(article_id):
    conn = get_db_connection()
    article = conn.execute("SELECT title FROM articles WHERE id=?", (article_id,)).fetchone()
    if not article:
        return "ไม่พบบทความ", 404

    conn.execute("DELETE FROM articles WHERE id=?", (article_id,))
    conn.commit()
    conn.close()

    # ลบไฟล์เสียงด้วย
    from lib.utils import sanitize_filename
    filename = f"{sanitize_filename(article['title'])}.mp3"
    audio_path = os.path.join("static", "audio", filename)
    if os.path.exists(audio_path):
        os.remove(audio_path)

    return redirect(url_for("admin_dashboard"))

from datetime import datetime

@app.route("/admin/add-category", methods=["GET", "POST"])
def add_article():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        category_id = request.form["category_id"]
        updated_at = datetime.now().isoformat()

        # 👉 1. บันทึกบทความลงฐานข้อมูล
        cursor.execute("""
            INSERT INTO articles (title, content, category_id, updated_at)
            VALUES (?, ?, ?, ?)
        """, (title, content, category_id, updated_at))
        conn.commit()

        # 👉 2. ดึง path ของหมวดหมู่
        cursor.execute("SELECT path FROM categories WHERE id = ?", (category_id,))
        category = cursor.fetchone()
        if category:
            category_path = category["path"]
            folder_path = os.path.join("data_base", category_path)
            os.makedirs(category_path, exist_ok=True)

            # 👉 3. สร้างชื่อไฟล์ .txt จากชื่อบทความ (sanitize)
            filename = f"{sanitize_filename(title)}.txt"
            file_path = os.path.join(category_path, filename)

            # 👉 4. เขียนไฟล์บทความลงไฟล์ .txt
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip())

        conn.close()
        flash("✅ เพิ่มบทความและสร้างไฟล์เรียบร้อยแล้ว", "success")
        return redirect(url_for("add_article"))

    # 👉 โหลดหมวดหมู่ (เฉพาะที่ไม่ขึ้นต้นด้วย h_)
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    all_categories = cursor.fetchall()
    categories = [
        (row["id"], row["name"])
        for row in all_categories
        if not row["name"].startswith("h_")
    ]

    conn.close()
    return render_template("add_article.html", categories=categories)

@app.context_processor
def inject_user():
    user = get_user(session['user_id']) if 'user_id' in session else None
    return dict(user=user)

@app.route('/like_post', methods=['POST'])
def like_post_route():
    return like_post()

if __name__ == "__main__":
    load_data()  # โหลดข้อมูลจากไฟล์ก่อน
    setup_app(app)
    app.run(debug=True)
