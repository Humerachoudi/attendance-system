import sqlite3
import os

# ------------------ Database Path ------------------ #
DB_PATH = os.path.join("backend", "attendance.db")

# ------------------ Database Connection ------------------ #
def get_connection():
    """Return a SQLite connection to the attendance database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------ Create Tables ------------------ #
def create_tables():
    """Create tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    # ✅ Users table (for both teacher & student)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('teacher', 'student')) NOT NULL
        )
    """)

    # ✅ Attendance table with GPS support
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            teacher_id INTEGER,
            subject TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            status TEXT DEFAULT 'Absent',
            qr_text TEXT,
            latitude REAL,
            longitude REAL,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (teacher_id) REFERENCES users (id)
        )
    """)

    # ✅ Subjects table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# ------------------ Initialize Database ------------------ #
def init_db():
    """Initialize database with tables and one default teacher."""
    create_tables()
    conn = get_connection()
    cur = conn.cursor()

    # ✅ Add default teacher if not exists
    cur.execute("SELECT * FROM users WHERE role='teacher'")
    teacher = cur.fetchone()
    if not teacher:
        cur.execute("""
            INSERT INTO users (reg_number, name, password, role)
            VALUES (?, ?, ?, ?)
        """, ("T001", "Default Teacher", "pass123", "teacher"))

    # ✅ Add default subjects
    subjects = [
        "R Programming",
        "Design and Analysis of Algorithms (DAA)",
        "Digital Marketing",
        "Software Engineering",
        "Cloud Computing",
        "Cyber Security",
        "R Programming Lab",
        "DAA Lab"
    ]

    for sub in subjects:
        cur.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (sub,))

    conn.commit()
    conn.close()

# ------------------ Run Automatically ------------------ #
if __name__ == "__main__":
    os.makedirs("backend", exist_ok=True)
    init_db()
    print("✅ Database initialized successfully.")
