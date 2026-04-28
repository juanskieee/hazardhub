"""
seed_admin.py  –  Run ONCE after importing schema.sql
This overwrites the placeholder admin password hash with a real one.

Usage:
    python seed_admin.py
"""

import MySQLdb
from werkzeug.security import generate_password_hash

# ── Connection settings (match app.py) ──
HOST     = "localhost"
USER     = "root"
PASSWORD = ""          # XAMPP default
DB       = "hazardhub"

ADMIN_EMAIL    = "admin@hazardhub.com"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME     = "Administrator"

def main():
    conn = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWORD, db=DB, charset="utf8mb4")
    cur  = conn.cursor()

    pw_hash = generate_password_hash(ADMIN_PASSWORD)

    # Upsert: update if exists, insert if not
    cur.execute("SELECT id FROM users WHERE email = %s", (ADMIN_EMAIL,))
    row = cur.fetchone()

    if row:
        cur.execute(
            "UPDATE users SET password_hash = %s, full_name = %s, id_number = 'ADMIN-00001' WHERE email = %s",
            (pw_hash, ADMIN_NAME, ADMIN_EMAIL)
        )
        print(f"✅  Admin password hash updated for {ADMIN_EMAIL}")
    else:
        cur.execute(
            """INSERT INTO users (full_name, email, password_hash, role, position, id_number)
               VALUES (%s, %s, %s, 'Admin', 'System Administrator', 'ADMIN-00001')""",
            (ADMIN_NAME, ADMIN_EMAIL, pw_hash)
        )
        print(f"✅  Admin account created for {ADMIN_EMAIL}")

    conn.commit()
    cur.close()
    conn.close()
    print("Done. You can now log in with:")
    print(f"  Email:    {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print(f"  Role:     Admin")

if __name__ == "__main__":
    main()
