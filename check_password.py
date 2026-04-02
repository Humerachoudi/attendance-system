import sqlite3, hashlib

# 👉 Change these
db_path = "backend/attendance.db"   # path to your database
teacher_reg = "T001"                # your teacher's reg_number
entered_password = "YourNewPassword"  # the new password you tried to set

# --- Check ---
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT password FROM users WHERE reg_number=?", (teacher_reg,))
row = cur.fetchone()
conn.close()

if not row:
    print("❌ Teacher not found in database.")
else:
    stored_hash = row[0]
    new_hash = hashlib.sha256(entered_password.strip().encode("utf-8")).hexdigest()
    print("Stored hash: ", stored_hash)
    print("Entered hash:", new_hash)
    print("\n✅ MATCH!" if stored_hash == new_hash else "\n❌ NOT MATCHING.")
