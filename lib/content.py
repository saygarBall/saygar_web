from flask import Blueprint, render_template, send_from_directory, request, abort, Response
import os
import sqlite3
from docx import Document
from gtts import gTTS
from lib.database import DB_FILE, get_db_connection
from lib.utils import sanitize_filename

content_bp = Blueprint("content", __name__)
DOWNLOAD_FOLDER = "downloads"
ARTICLE_FOLDER = "articles"
AUDIO_FOLDER = "static/audio"

def get_file_size(file_path):
    if os.path.exists(file_path):
        size = os.path.getsize(file_path) / (1024 * 1024)
        return f"{size:.2f} MB"
    return "ไม่พบไฟล์"

def convert_docx_to_html(file_path):
    doc = Document(file_path)
    html_content = ""
    for para in doc.paragraphs:
        text = para.text
        if text.startswith("download_file="):
            filename = text.split("=")[1].strip()
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            file_size = get_file_size(file_path)
            download_link = f'<a href="{request.host_url}download/{filename}" class="btn btn-success">📥 Download {filename} ({file_size})</a>'
            html_content += f"<p>{download_link}</p>\n"
        else:
            html_content += f"<p>{text}</p>\n"
    return html_content

@content_bp.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        abort(404, description="ไม่พบไฟล์")
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@content_bp.route("/content/<int:article_id>")
def content(article_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content, category_id FROM articles WHERE id=?", (article_id,))
    article = cursor.fetchone()
    conn.close()

    if not article:
        return "ไม่พบบทความนี้"

    title, content, category_id = article
    new_content = []
    lines = content.split("\n")
    for line in lines:
        if line.startswith("download_file="):
            filename = line.split("=")[1].strip()
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            file_size = get_file_size(file_path)
            file_ext = filename.split(".")[-1].lower()

            if file_ext in ["mp3", "wav", "ogg"]:
                player_html = f'''
                <audio id="{filename}" controls>
                    <source src="{request.host_url}download/{filename}" type="audio/{file_ext}">
                    Your browser does not support the audio tag.
                </audio>
                '''
            elif file_ext in ["mp4", "mov"]:
                player_html = f'''
                <video id="{filename}" width="600" controls>
                    <source src="{request.host_url}download/{filename}" type="video/{file_ext}">
                    Your browser does not support the video tag.
                </video>
                '''
            else:
                player_html = f'<a href="{request.host_url}download/{filename}" class="btn btn-success">📥 Download {filename} ({file_size})</a>'

            new_content.append(player_html)

        elif line.startswith("media_file="):
            filename = line.split("=")[1].strip()
            file_path = os.path.join(ARTICLE_FOLDER, filename)
            file_size = get_file_size(file_path)
            file_ext = filename.split(".")[-1].lower()
            media_url = f"{request.host_url}media/{filename}"

            if file_ext in ["mp3", "wav", "ogg"]:
                player_html = f'''
                <audio id="{filename}" controls>
                    <source src="{media_url}" type="audio/{file_ext}">
                    Your browser does not support the audio tag.
                </audio>
                '''
            elif file_ext in ["mp4", "mov"]:
                player_html = f'''
                <video id="{filename}" width="600" controls>
                    <source src="{media_url}" type="video/{file_ext}">
                    Your browser does not support the video tag.
                </video>
                '''
            else:
                player_html = f'<a href="{media_url}" class="btn btn-success">📥 Download {filename} ({file_size})</a>'

            new_content.append(player_html)
        else:
            new_content.append(line)

    content_html = "<br>".join(new_content)

    # ✅ สร้าง path ไฟล์เสียงที่เกี่ยวข้อง
    audio_filename = f"{sanitize_filename(title)}.mp3"
    tts_path = os.path.join(AUDIO_FOLDER, audio_filename)
    tts_url = f"/{tts_path}" if os.path.exists(tts_path) else None

    return render_template("content.html", title=title, content=content_html, category_id=category_id, tts_url=tts_url, article_id=article_id)

@content_bp.route("/tts/<int:article_id>")
def generate_tts(article_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM articles WHERE id=?", (article_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        abort(404, description="ไม่พบบทความนี้")

    text = row[0]
    tts = gTTS(text=text, lang="th")
    os.makedirs(AUDIO_FOLDER, exist_ok=True)
    audio_filename = f"article_{article_id}.mp3"
    file_path = os.path.join(AUDIO_FOLDER, audio_filename)
    tts.save(file_path)

    return send_from_directory(AUDIO_FOLDER, audio_filename)

@content_bp.route("/media/<filename>")
def media_file(filename):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id FROM articles WHERE content LIKE ?", (f"media_file={filename}",))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        abort(404, description="ไม่พบไฟล์")

    category_id = row["category_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM categories WHERE id = ?", (category_id,))
    category = cursor.fetchone()
    conn.close()

    if category is None:
        abort(404, description="ไม่พบหมวดหมู่")

    category_path = category["path"]
    file_path = os.path.join(category_path, filename)

    if not os.path.exists(file_path):
        abort(404, description="ไม่พบไฟล์")

    return send_from_directory(category_path, filename, mimetype="audio/mpeg" if filename.endswith(".mp3") else "video/mp4")
