import sqlite3
import os

def migrate():
    # Detect environment
    if os.path.exists('/app/data'):
        DATABASE_DIR = "/app/data"
    else:
        DATABASE_DIR = "data"

    db_path = os.path.join(DATABASE_DIR, "database.db")

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(scheduled_tasks)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'employee_id' not in columns:
            cursor.execute("""
                ALTER TABLE scheduled_tasks
                ADD COLUMN employee_id INTEGER
            """)
            print("✓ Added employee_id column to scheduled_tasks")
        else:
            print("✓ employee_id column already exists in scheduled_tasks")

        conn.commit()
        print("✓ Migration completed successfully")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
