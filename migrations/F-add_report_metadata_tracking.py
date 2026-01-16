"""
Migration: Add Report Metadata Tracking

This migration adds metadata tracking to the DailyBalance table to record:
- Who created/finalized the report (user or scheduled task)
- When the report was finalized
- Who last edited the report

New columns:
- created_by_user_id: Foreign key to users table (NULL if created by scheduled task)
- created_by_source: 'user' or 'scheduled_task' to indicate the source
- edited_by_user_id: Foreign key to users table for tracking edits
- finalized_at: Timestamp of when the report was finalized

Database Location:
- Docker: /app/data/database.db
- Bare metal: <project_root>/data/database.db

Usage:
    python migrations/F-add_report_metadata_tracking.py
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

if os.path.exists("/app"):
    os.chdir("/app")
else:
    os.chdir(project_root)

sys.path.insert(0, project_root)

from sqlalchemy import inspect, text
from app.database import engine

def migrate():
    """Add metadata tracking columns to daily_balance table"""
    inspector = inspect(engine)

    # Check if daily_balance table exists
    if 'daily_balance' not in inspector.get_table_names():
        print("daily_balance table does not exist yet. Skipping migration.")
        return

    columns = [col['name'] for col in inspector.get_columns('daily_balance')]

    with engine.connect() as conn:
        try:
            # Add created_by_user_id column if it doesn't exist
            if "created_by_user_id" not in columns:
                conn.execute(text("""
                    ALTER TABLE daily_balance
                    ADD COLUMN created_by_user_id INTEGER
                """))
                print("✓ Added created_by_user_id column to daily_balance")

            # Add created_by_source column if it doesn't exist
            if "created_by_source" not in columns:
                conn.execute(text("""
                    ALTER TABLE daily_balance
                    ADD COLUMN created_by_source TEXT DEFAULT 'user'
                """))
                print("✓ Added created_by_source column to daily_balance")

            # Add edited_by_user_id column if it doesn't exist
            if "edited_by_user_id" not in columns:
                conn.execute(text("""
                    ALTER TABLE daily_balance
                    ADD COLUMN edited_by_user_id INTEGER
                """))
                print("✓ Added edited_by_user_id column to daily_balance")

            # Add finalized_at column if it doesn't exist
            if "finalized_at" not in columns:
                conn.execute(text("""
                    ALTER TABLE daily_balance
                    ADD COLUMN finalized_at TEXT
                """))
                print("✓ Added finalized_at column to daily_balance")

            conn.commit()
            print("✓ Migration F completed successfully")

        except Exception as e:
            conn.rollback()
            print(f"✗ Migration F failed: {e}")
            raise

if __name__ == "__main__":
    migrate()
