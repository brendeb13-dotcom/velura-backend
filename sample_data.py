import sqlite3

conn = sqlite3.connect("velura.db")
cursor = conn.cursor()

# Add Parlours
cursor.executemany(
    "INSERT INTO parlours (name, location, rating) VALUES (?, ?, ?)",
    [
        ("Velura Glow Salon", "MG Road", 4.5),
        ("Chic Style Hub", "Indiranagar", 4.1),
        ("Royal Beauty Lounge", "Whitefield", 4.8)
    ]
)

# Add Services
cursor.executemany(
    "INSERT INTO services (title, price, image) VALUES (?, ?, ?)",
    [
        ("Haircut", 499, "haircut.png"),
        ("Facial", 399, "facial.png"),
        ("Spa", 599, "spa.png"),
        ("Makeup", 799, "makeup.png")
    ]
)

# Link Exclusive Services
cursor.executemany(
    "INSERT INTO parlour_services (parlour_id, service_id) VALUES (?, ?)",
    [
        (1, 1),
        (1, 2),   # Glow Salon offers Haircut & Facial
        (2, 4),   # Chic Style Hub offers Makeup only
        (3, 2),
        (3, 3)    # Royal Beauty offers Facial & Spa
    ]
)

conn.commit()
conn.close()

print("✅ Sample data inserted!")
