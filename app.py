
from flask import Flask, render_template, request, redirect, jsonify
from scrape import get_connection
import sqlite3
import os
import re

app = Flask(__name__)

def is_valid_guide_id(guide_id):
    return bool(re.match(r"^\d{1,32}$", guide_id))

def render_index(guide_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name FROM guides WHERE id = ?
    """, (guide_id,))
    row = cur.fetchone()
    conn.close()
    return render_template("index.html", guide=row)

@app.route("/", methods=["GET"])
def index():
    return render_index()

@app.route("/<int:guide_id>")
def guide_page(guide_id):
    return render_index(guide_id=guide_id)

@app.route("/add-guide", methods=["POST"])
def add_guide():
    guide_id = request.form.get("guide_id").strip()
    if not is_valid_guide_id(guide_id):
        return render_template("index.html", error="The guide ID must consist of numbers only and not exceed 32 characters.")
    from scrape import get_guide_name
    name = get_guide_name(guide_id)
    if name:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO guides (id, name) VALUES (?, ?)", (guide_id, name))
        conn.commit()
        conn.close()
    return redirect("./")

@app.route("/data/<guide_id>")
def data(guide_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, likes, visitors, favorites FROM stats
        WHERE guide_id = ? ORDER BY timestamp ASC
    """, (guide_id,))
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if len(query) < 3:
        return jsonify([])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name FROM guides 
        WHERE name LIKE ? 
        ORDER BY id DESC 
        LIMIT 100
    """, (f"%{query}%",))
    results = [{"id": row["id"], "name": row["name"]} for row in cur.fetchall()]
    conn.close()
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
