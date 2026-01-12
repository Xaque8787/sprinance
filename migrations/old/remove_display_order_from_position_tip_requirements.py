import sqlite3
import os

def migrate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    if not os.path.exists(db_path):
        print("Database does not exist. Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(position_tip_requirements)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'display_order' in columns:
            print("Removing display_order column from position_tip_requirements table...")

            cursor.execute("SELECT position_id, tip_requirement_id FROM position_tip_requirements")
            existing_data = cursor.fetchall()

            cursor.execute("DROP TABLE position_tip_requirements")

            cursor.execute("""
                CREATE TABLE position_tip_requirements (
                    position_id INTEGER NOT NULL,
                    tip_requirement_id INTEGER NOT NULL,
                    PRIMARY KEY (position_id, tip_requirement_id),
                    FOREIGN KEY (position_id) REFERENCES positions(id),
                    FOREIGN KEY (tip_requirement_id) REFERENCES tip_entry_requirements(id)
                )
            """)

            for position_id, tip_requirement_id in existing_data:
                cursor.execute(
                    "INSERT INTO position_tip_requirements (position_id, tip_requirement_id) VALUES (?, ?)",
                    (position_id, tip_requirement_id)
                )

            print(f"Migrated {len(existing_data)} position-requirement associations")
        else:
            print("display_order column does not exist in position_tip_requirements table")

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
