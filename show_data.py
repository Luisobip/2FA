import sqlite3
from config import Config  # o directamente pon el nombre del archivo .db

def show_tables(db_name=None):
    db_name = db_name or Config.DATABASE_NAME
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    print("=== Tabla: users ===")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        print(user)

    print("\n=== Tabla: login_attempts ===")
    cursor.execute("SELECT * FROM login_attempts")
    attempts = cursor.fetchall()
    for attempt in attempts:
        print(attempt)

    conn.close()

if __name__ == "__main__":
    show_tables()
