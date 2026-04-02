import sqlite3

DB_PATH = "backend/attendance.db"

def print_table(table_name):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    print(f"\n--- {table_name.upper()} ---")
    if rows:
        for r in rows:
            print(dict(r))
    else:
        print("No records found.")
    conn.close()

if __name__ == "__main__":
    print_table("users")
    print_table("students")
    print_table("teachers")
