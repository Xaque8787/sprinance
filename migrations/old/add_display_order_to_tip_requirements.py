import sqlite3
import os

def migrate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    if not os.path.exists(db_path):
        print("Database does not exist. Will be created with display_order column.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(tip_entry_requirements)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'display_order' not in columns:
            print("Adding display_order column to tip_entry_requirements table...")
            cursor.execute("ALTER TABLE tip_entry_requirements ADD COLUMN display_order INTEGER DEFAULT 0")

            print("Setting default display order values...")
            cursor.execute("SELECT id FROM tip_entry_requirements ORDER BY id")
            for idx, row in enumerate(cursor.fetchall()):
                cursor.execute("UPDATE tip_entry_requirements SET display_order = ? WHERE id = ?", (idx, row[0]))

            print("Display order values set successfully")
        else:
            print("display_order column already exists")

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
