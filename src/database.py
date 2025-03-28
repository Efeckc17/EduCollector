import sqlite3

def init_db(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT DEFAULT 'User', profile_img TEXT, default_language TEXT DEFAULT 'English')")
    c.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, language TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, content TEXT, url TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    c.execute("SELECT COUNT(*) FROM user")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO user (name, profile_img, default_language) VALUES (?, ?, ?)", ("User", "", "English"))
        conn.commit()
    conn.close()

def load_user(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT id, name, profile_img, default_language FROM user LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "profile_img": row[2] or "", "default_language": row[3] or "English"}
    return {"id": None, "name": "User", "profile_img": "", "default_language": "English"}

def record_search(db, topic, lang_code):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO history (topic, language) VALUES (?, ?)", (topic, lang_code))
    conn.commit()
    conn.close()

def save_article(db, topic, content, url):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO articles (topic, content, url) VALUES (?, ?, ?)", (topic, content, url))
    conn.commit()
    conn.close()
