import sqlite3
import os

# --- Path to your database ---
db_path = os.path.join("backend", "attendance.db")

if not os.path.exists(db_path):
    print(f"⚠️ Database not found at: {db_path}")
    exit()

print(f"Checking database: {db_path}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check tables
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("\n📋 Tables:", [t[0] for t in tables])

# Check users
try:
    users = cur.execute("SELECT id, reg_number, name, role FROM users LIMIT 10;").fetchall()
    print(f"\n👤 Found {len(users)} sample users:")
    for u in users:
        print(f"   {u[1]} — {u[2]} ({u[3]})")
except Exception as e:
    print("\n⚠️ Error reading users table:", e)

# Check attendance table
try:
    attendance = cur.execute("SELECT COUNT(*) FROM attendance;").fetchone()[0]
    print(f"\n🗓️ Attendance records: {attendance}")
except Exception as e:
    print("\n⚠️ Error reading attendance table:", e)

conn.close()
print("\n✅ Database check complete!")
