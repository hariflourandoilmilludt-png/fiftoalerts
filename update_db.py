import sqlite3
import os

DB_FILE = "tradingview_alerts.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found. Skipping migration.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    columns = [
        ("quantman_buy_url", "TEXT"),
        ("quantman_sell_url", "TEXT"),
        ("quantman_close_url", "TEXT")
    ]

    print("Checking for missing columns...")
    try:
        # Get existing columns
        cursor.execute("PRAGMA table_info(instruments)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        for col_name, col_type in columns:
            if col_name not in existing_columns:
                print(f"Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE instruments ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists.")
        
        conn.commit()
        print("Migration complete.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
