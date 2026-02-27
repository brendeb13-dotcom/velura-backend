import sqlite3

conn = sqlite3.connect("velura.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;")
    print("✅ is_admin column added")
except Exception as e:
    print("⚠️", e)

cur.execute("UPDATE users SET is_admin = 1 WHERE email = 'test@velura.com';")
conn.commit()

for row in cur.execute("SELECT id, email, is_admin FROM users"):
    print(row)

conn.close()