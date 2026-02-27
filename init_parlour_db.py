import sqlite3

conn = sqlite3.connect("velura.db")
cursor = conn.cursor()

# Parlours table
cursor.execute("""
CREATE TABLE IF NOT EXISTS parlours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    rating REAL DEFAULT 0
)
""")

# Services table
cursor.execute("""
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    image TEXT
)
""")

# Mapping table for exclusive services
cursor.execute("""
CREATE TABLE IF NOT EXISTS parlour_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parlour_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    FOREIGN KEY (parlour_id) REFERENCES parlours(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
)
""")

conn.commit()
conn.close()

print("✅ Parlour & Services tables created successfully!")
