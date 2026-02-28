from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from functools import wraps
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from passlib.context import CryptContext

# ---------------- APP SETUP ----------------

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

app.config["JWT_SECRET_KEY"] = "velura-super-secret-key"
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True

jwt = JWTManager(app)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# ---------------- DATABASE ----------------

def get_db_connection():
    conn = sqlite3.connect("velura.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parlours (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        image TEXT,
        rating REAL DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parlour_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        image TEXT,
        FOREIGN KEY (parlour_id) REFERENCES parlours (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        parlour_id INTEGER NOT NULL,
        service_name TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (parlour_id) REFERENCES parlours (id)
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ---------------- ADMIN DECORATOR ----------------

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        conn.close()

        if not user or user["is_admin"] != 1:
            return jsonify({"error": "Admin access required"}), 403

        return fn(*args, **kwargs)

    return wrapper

# ---------------- SEED DATA ----------------

def seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM parlours")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO parlours (name, location, image, rating) VALUES (?, ?, ?, ?)",
            [
                ("Velura Luxe Salon", "Bangalore", "salon1.jpg", 4.8),
                ("Glow & Grace", "Mumbai", "salon2.jpg", 4.6),
                ("Urban Touch", "Delhi", "salon3.jpg", 4.7),
            ]
        )

    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO services (parlour_id, name, price, image) VALUES (?, ?, ?, ?)",
            [
                (1, "Haircut", 499, "haircut.jpg"),
                (1, "Facial", 799, "facial.jpg"),
                (1, "Spa", 1299, "spa.jpg"),
                (2, "Haircut", 399, "haircut.jpg"),
                (2, "Makeup", 1599, "makeup.jpg"),
                (3, "Haircut", 599, "haircut.jpg"),
                (3, "Hair Coloring", 1999, "coloring.jpg"),
            ]
        )

    conn.commit()
    conn.close()


seed_data()

# ---------------- BASIC ROUTES ----------------

@app.route("/")
def home():
    return jsonify({"message": "VELURA Backend Running"}), 200


@app.route("/ping")
def ping():
    return jsonify({"status": "pong"}), 200

# ---------------- AUTH ----------------

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    hashed = pwd_context.hash(data["password"])

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (data["email"], hashed)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if not user or not pwd_context.verify(password, user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user["id"]))

    return jsonify({
        "access_token": access_token,
        "is_admin": bool(user["is_admin"])
    }), 200

# ---------------- USER APIs ----------------

@app.route("/parlours", methods=["GET"])
def get_parlours():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM parlours").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/parlours/<int:parlour_id>/services", methods=["GET"])
def get_services(parlour_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM services WHERE parlour_id = ?",
        (parlour_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/book", methods=["POST"])
@jwt_required()
def book():
    user_id = get_jwt_identity()
    data = request.get_json()

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO appointments
        (user_id, parlour_id, service_name, date, time)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, data["parlour_id"], data["service_name"], data["date"], data["time"])
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Appointment booked"}), 200


@app.route("/appointments", methods=["GET"])
@jwt_required()
def appointments():
    user_id = get_jwt_identity()

    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM appointments WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows]), 200


@app.route("/appointments/<int:appt_id>", methods=["DELETE"])
@jwt_required()
def cancel(appt_id):
    user_id = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM appointments WHERE id = ? AND user_id = ?",
        (appt_id, user_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Appointment cancelled"}), 200

# ---------------- ADMIN APIs ----------------

@app.route("/admin/parlours", methods=["POST"])
@admin_required
def admin_add_parlour():
    data = request.get_json()

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO parlours (name, location, image, rating) VALUES (?, ?, ?, ?)",
        (data["name"], data["location"], data.get("image"), data.get("rating", 0))
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Parlour added"}), 201


@app.route("/admin/services", methods=["POST"])
@admin_required
def admin_add_service():
    data = request.get_json()

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO services (parlour_id, name, price, image) VALUES (?, ?, ?, ?)",
        (data["parlour_id"], data["name"], data["price"], data.get("image"))
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Service added"}), 201

# ---------------- RUN ----------------

@app.route("/debug/users")
def debug_users():
    conn = get_db_connection()
    rows = conn.execute("SELECT id, email, is_admin FROM users").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
