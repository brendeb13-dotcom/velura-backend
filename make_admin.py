import sqlite3

conn = sqlite3.connect("velura.db")
cursor = conn.cursor()

cursor.execute("UPDATE users SET is_admin = 1 WHERE email = 'admin@velura.com'")

conn.commit()
conn.close()

print("Admin granted successfully")
