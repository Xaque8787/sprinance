"""
Migration script to add tip_out field to daily_employee_entries table.

Changes:
1. Add tip_out column to daily_employee_entries table with default value 0.0

This field allows tracking tip-outs, which are subtracted from the take-home tips total.
"""
import sqlite3
import os

def migrate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    print(f"Looking for database at: {db_path}")

    if not os.path.exists(db_path):
        print("Database does not exist. No migration needed.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting migration to add tip_out field...")

        # Check if tip_out column already exists
        cursor.execute("PRAGMA table_info(daily_employee_entries)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'tip_out' not in columns:
            print("Adding tip_out column to daily_employee_entries...")
            cursor.execute("""
                ALTER TABLE daily_employee_entries
                ADD COLUMN tip_out REAL DEFAULT 0.0
            """)
            print("Successfully added tip_out column")
        else:
            print("tip_out column already exists")

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
