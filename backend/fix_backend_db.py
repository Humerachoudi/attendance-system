import sqlite3
import os

# ✅ Correct database path (since attendance.db is one folder up)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "attendance.db")
DB_PATH = os.path.abspath(DB_PATH)

def fix_attendance_table():
    print(f"🔍 Checking database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if attendance table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance';")
    if not cur.fetchone():
        print("⚠️ 'attendance' table not found! Creating it now...")
        cur.execute("""
            CREATE TABLE attendance (
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
        conn.commit()
        print("✅ Created new 'attendance' table with GPS columns.")
    else:
        print("✅ 'attendance' table found — checking GPS columns...")
        cur.execute("PRAGMA table_info(attendance);")
        existing_columns = [row[1] for row in cur.fetchall()]

        added = False
        for col in ["latitude", "longitude"]:
            if col not in existing_columns:
                cur.execute(f"ALTER TABLE attendance ADD COLUMN {col} REAL;")
                print(f"🆕 Added column: {col}")
                added = True

        if not added:
            print("✅ GPS columns already exist — no changes needed.")
        conn.commit()

    conn.close()
    print("\n🎯 Database check complete! You’re ready to restart your FastAPI app.")

if __name__ == "__main__":
    fix_attendance_table()
