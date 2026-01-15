import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Create scheduled_tasks table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                schedule_type TEXT NOT NULL,
                cron_expression TEXT,
                interval_value INTEGER,
                interval_unit TEXT,
                start_date TEXT,
                end_date TEXT,
                date_range_type TEXT,
                email_list TEXT,
                bypass_opt_in INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run_at TIMESTAMP,
                next_run_at TIMESTAMP
            )
        """))

        # Create task_executions table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS task_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT NOT NULL,
                error_message TEXT,
                result_data TEXT,
                FOREIGN KEY (task_id) REFERENCES scheduled_tasks (id) ON DELETE CASCADE
            )
        """))

        # Create index for task_executions cleanup
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_task_executions_task_id_started
            ON task_executions(task_id, started_at DESC)
        """))

        db.commit()
        print("✓ Scheduler tables created successfully")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
