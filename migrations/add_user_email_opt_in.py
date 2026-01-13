import sqlite3
import os

def migrate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    if not os.path.exists(db_path):
        print("Database not found. Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT opt_in_daily_reports FROM users LIMIT 1")
        print("Column 'opt_in_daily_reports' already exists. Skipping migration.")
    except sqlite3.OperationalError:
        print("Adding opt_in_daily_reports column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN opt_in_daily_reports BOOLEAN DEFAULT 0")
        conn.commit()
        print("opt_in_daily_reports column added successfully.")

    try:
        cursor.execute("SELECT opt_in_tip_reports FROM users LIMIT 1")
        print("Column 'opt_in_tip_reports' already exists. Skipping migration.")
    except sqlite3.OperationalError:
        print("Adding opt_in_tip_reports column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN opt_in_tip_reports BOOLEAN DEFAULT 0")
        conn.commit()
        print("opt_in_tip_reports column added successfully.")

    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
