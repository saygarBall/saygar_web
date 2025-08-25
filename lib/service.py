import sqlite3
from datetime import datetime
from flask import Blueprint, render_template
from lib.database import DB_FILE

service_bp = Blueprint("service", __name__)

@service_bp.route("/service/<int:category_id>")
def service(category_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM categories WHERE id=?", (category_id,))
    category_name = cursor.fetchone()[0]

    cursor.execute("SELECT id, name FROM categories WHERE parent_id=?", (category_id,))
    subcategories = cursor.fetchall()

    cursor.execute("SELECT id, title, updated_at FROM articles WHERE category_id=?", (category_id,))
    articles = cursor.fetchall()

    conn.close()
    return render_template("service.html", category_name=category_name, subcategories=subcategories, articles=articles)
