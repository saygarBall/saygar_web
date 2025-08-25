from flask import Blueprint, render_template, request
from lib.database import get_db_connection

search_bp = Blueprint("search", __name__)

@search_bp.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()

    if not query:
        return render_template("search.html", query=query, results=[])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, content FROM articles
        WHERE title LIKE ? OR content LIKE ?
    """, (f"%{query}%", f"%{query}%"))

    results = cursor.fetchall()
    conn.close()

    return render_template("search.html", query=query, results=results)
