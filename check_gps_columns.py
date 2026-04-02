import sqlite3

db_path = "attendance.db"  # since it's in your main folder
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# ✅ Check if attendance table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance';")
table = cur.fetchone()

if not table:
    print("⚠️ 'attendance' table not found! Creating it now...")
    cur.execute("""
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            teacher_id INTEGER,
            subject TEXT,
            date TEXT,
            time TEXT,
            status TEXT,
            qr_text TEXT,
            latitude REAL,
            longitude REAL
        );
    """)
    print("✅ Created new 'attendance' table with GPS columns.")
else:
    print("✅ 'attendance' table found. Checking columns...")
    cur.execute("PRAGMA table_info(attendance);")
    columns = [row[1] for row in cur.fetchall()]
    print("Current columns:", columns)

    # Add missing GPS columns if needed
    if "latitude" not in columns:
        cur.execute("ALTER TABLE attendance ADD COLUMN latitude REAL;")
        print("✅ Added 'latitude' column.")
    if "longitude" not in columns:
        cur.execute("ALTER TABLE attendance ADD COLUMN longitude REAL;")
        print("✅ Added 'longitude' column.")

conn.commit()
conn.close()
print("\n🎯 Database check complete! You’re ready to restart your FastAPI app.")
