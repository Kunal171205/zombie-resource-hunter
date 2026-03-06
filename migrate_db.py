import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'app', 'history.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. No migration needed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Adding 'total_instances_checked' column to 'scans' table...")
        cursor.execute("ALTER TABLE scans ADD COLUMN total_instances_checked INTEGER DEFAULT 0")
        conn.commit()
        print("Migration successful!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column already exists. Skipping.")
        else:
            print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
