import sqlite3
import os

def migrate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    if not os.path.exists(db_path):
        print("Database does not exist. Will be created with is_deduction column.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(financial_line_item_templates)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'is_deduction' not in columns:
            print("Adding is_deduction column to financial_line_item_templates table...")
            cursor.execute("ALTER TABLE financial_line_item_templates ADD COLUMN is_deduction BOOLEAN DEFAULT 0")
            print("is_deduction column added successfully")
        else:
            print("is_deduction column already exists")

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
