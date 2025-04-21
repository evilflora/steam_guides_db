#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

with open("/var/log/cron.log", "a") as f:
    f.write(f"scrape.py lancé à {datetime.now()}\n")

DB_PATH = "/app/data.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_guide_name(guide_id):
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={guide_id}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, 'html.parser')
    title_el = soup.select_one(".workshopItemTitle")
    return title_el.text.strip() if title_el else None

def scrape_all():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM guides")
    guide_rows = cur.fetchall()

    for row in guide_rows:
        gid = row["id"]
        current_name = row["name"]

        try:
            url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={gid}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            new_name = get_guide_name(gid)
            if new_name and new_name != current_name:
                cur.execute("UPDATE guides SET name = ? WHERE id = ?", (new_name, gid))
                conn.commit()

            stats_table = soup.select(".stats_table td")

            if len(stats_table) >= 4:
                visitors = int(stats_table[0].text.replace(",", "").strip())
                favorites = int(stats_table[2].text.replace(",", "").strip())
            else:
                print(f"[{gid}] stats_table incomplete.")
                continue

            rating_text = soup.select_one(".numRatings")

            if rating_text:
                likes = int(rating_text.text.replace(",", "").replace("ratings", "").strip())
            else:
                likes = 0

            timestamp = datetime.now().replace(second=0, microsecond=0)

            cur.execute("""
                INSERT INTO stats (guide_id, timestamp, likes, visitors, favorites)
                VALUES (?, ?, ?, ?, ?)
            """, (gid, timestamp, likes, visitors, favorites))

            conn.commit()

        except Exception as e:
            print(f"[{gid}] Erreur lors du scraping : {e}")

    conn.close()

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS guides (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guide_id INTEGER,
            timestamp TEXT,
            likes INTEGER,
            visitors INTEGER,
            favorites INTEGER,
            FOREIGN KEY (guide_id) REFERENCES guides(id)
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    scrape_all()
