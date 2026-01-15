"""
Migration: Add employee_id column to scheduled_tasks

This migration adds a new integer column 'employee_id' to the scheduled_tasks table.
This attribute allows scheduled tasks to be associated with a specific employee.

Database Location:
- Docker: /app/data/database.db
- Bare metal: <project_root>/data/database.db

Usage:
    python migrations/add_employee_id_to_scheduled_tasks.py
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

    if 'employee_id' not in columns:
        print("Adding 'employee_id' column to scheduled_tasks table...")
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE scheduled_tasks
                ADD COLUMN employee_id INTEGER;
            """))
            conn.commit()
        print("✓ Migration completed: employee_id column added")
    else:
        print("✓ Column 'employee_id' already exists, skipping migration")

if __name__ == "__main__":
    run_migration()
