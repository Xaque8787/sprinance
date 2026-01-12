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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='position_tip_requirements'")
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            print("Creating position_tip_requirements table with display_order column...")
            cursor.execute("""
                CREATE TABLE position_tip_requirements (
                    position_id INTEGER NOT NULL,
                    tip_requirement_id INTEGER NOT NULL,
                    display_order INTEGER DEFAULT 0,
                    PRIMARY KEY (position_id, tip_requirement_id),
                    FOREIGN KEY (position_id) REFERENCES positions(id),
                    FOREIGN KEY (tip_requirement_id) REFERENCES tip_entry_requirements(id)
                )
            """)
        else:
            cursor.execute("PRAGMA table_info(position_tip_requirements)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'display_order' not in columns:
                print("Adding display_order column to existing position_tip_requirements table...")
                cursor.execute("ALTER TABLE position_tip_requirements ADD COLUMN display_order INTEGER DEFAULT 0")
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
