import sqlite3

db_path = "backend/attendance.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# --- Check if 'subject' column already exists ---
cur.execute("PRAGMA table_info(attendance);")
columns = [col[1] for col in cur.fetchall()]

if "subject" not in columns:
    print("🛠 Adding 'subject' column to attendance table...")
    cur.execute("ALTER TABLE attendance ADD COLUMN subject TEXT;")
    conn.commit()
    print("✅ Column 'subject' added successfully!")
else:
    print("✅ 'subject' column already exists, no change made.")

conn.close()
