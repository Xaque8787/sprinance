"""
Migration: Add starts_at column to scheduled_tasks

This migration adds a new timestamp column 'starts_at' to the scheduled_tasks table.
This attribute allows users to set a specific starting reference point for interval-based
schedules, ensuring that tasks run at consistent intervals from the specified start time.

Database Location:
- Docker: /app/data/database.db
- Bare metal: <project_root>/data/database.db

Usage:
    python migrations/add_starts_at_to_scheduled_tasks.py
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

def run_migration():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('scheduled_tasks')]

    if 'starts_at' not in columns:
        print("Adding 'starts_at' column to scheduled_tasks table...")
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE scheduled_tasks
                ADD COLUMN starts_at TIMESTAMP;
            """))
            conn.commit()
        print("✓ Migration completed: starts_at column added")
    else:
        print("✓ Column 'starts_at' already exists, skipping migration")

if __name__ == "__main__":
    run_migration()
