#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

ENABLE_LOGGING = True  # Active/désactive les logs détaillés
DB_PATH = "/app/data.db"

def log_request_info(start_time, end_time, content_length, url):
    if ENABLE_LOGGING:
        print(f"--- Log for : {url} ---")
        print(f"Start time  : {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time    : {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration    : {(end_time - start_time).total_seconds():.4f} seconds")
        print(f"Page size   : {content_length} B")
        print("-----------------------------------\n")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_html(session, url):
    start_time = datetime.now()
    try:
        response = session.get(url)
        response.raise_for_status()
        end_time = datetime.now()

        content_length = len(response.content)
        log_request_info(start_time, end_time, content_length, url)

        return response.text
    except Exception as e:
        end_time = datetime.now()
        log_request_info(start_time, end_time, 0, url)
        raise e

def scrape_all():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM guides")
    guide_rows = cur.fetchall()

    with requests.Session() as session:
        # Définir un User-Agent global
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

        for row in guide_rows:
            gid = row["id"]
            current_name = row["name"]

            try:
                url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={gid}"
                html = fetch_html(session, url)
                soup = BeautifulSoup(html, "html.parser")

                title_el = soup.select_one(".workshopItemTitle")
                new_name = title_el.text.strip() if title_el else None

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
                likes = int(rating_text.text.replace(",", "").replace("ratings", "").strip()) if rating_text else 0

                timestamp = int(datetime.now().timestamp())

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
            timestamp INTEGER,
            likes INTEGER,
            visitors INTEGER,
            favorites INTEGER,
            FOREIGN KEY (guide_id) REFERENCES guides(id)
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    with open("/var/log/cron.log", "a") as f:
        f.write(f"scrape.py lancé à {datetime.now()}\n")
    init_db()
    scrape_all()
