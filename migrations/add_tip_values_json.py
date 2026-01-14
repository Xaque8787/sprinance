"""
Migration: Add tip_values JSON column to DailyEmployeeEntry

This migration adds a JSON column to store dynamic tip requirement values,
allowing the system to handle any number of custom tip fields without
requiring database schema changes.

The tip_values column will store a dictionary of field_name: value pairs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal

def run_migration():
    db = SessionLocal()
    try:
        # Check if column exists by trying to query it
        try:
            check_query = text("SELECT tip_values FROM daily_employee_entries LIMIT 1")
            db.execute(check_query)
            print("Column tip_values already exists, skipping")
        except Exception:
            # Column doesn't exist, add it
            alter_query = text("""
                ALTER TABLE daily_employee_entries
                ADD COLUMN tip_values TEXT DEFAULT '{}'
            """)
            db.execute(alter_query)
            db.commit()
            print("Added tip_values JSON column to daily_employee_entries")

        print("Migration completed successfully")

    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
