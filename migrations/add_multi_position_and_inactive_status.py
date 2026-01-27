#!/usr/bin/env python3
"""
Multi-Position & Inactive Status Migration

This script sets up the database and applies the multi-position migration.
Run this once after updating to the multi-position version.

Changes:
1. Add is_active column to employees table (default TRUE)
2. Create employee_position_schedule table for multi-position support
3. Migrate existing data (employee.position_id + scheduled_days → employee_position_schedule)
4. Add position_id to daily_employee_entries for tracking which position was worked
5. Make employee.position_id nullable (it's deprecated, kept for backward compatibility)

Historical data preservation:
- All existing daily_employee_entry records remain untouched
- Old employee.position_id and scheduled_days columns kept for rollback safety
"""
import sys
import os
import sqlite3
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, database_exists

def migrate():
    """
    Execute the multi-position migration on existing database.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    if not os.path.exists(db_path):
        print("Database does not exist. Will be created with new schema.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Add is_active column to employees table
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'is_active' not in columns:
            print("Adding is_active column to employees table...")
            cursor.execute("ALTER TABLE employees ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✓ is_active column added (all existing employees set to active)")
        else:
            print("✓ is_active column already exists")

        # Step 2: Create employee_position_schedule table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_position_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                position_id INTEGER NOT NULL,
                days_of_week TEXT DEFAULT '[]',
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE RESTRICT,
                UNIQUE(employee_id, position_id)
            )
        """)
        print("✓ employee_position_schedule table created")

        # Step 3: Migrate existing data
        cursor.execute("""
            SELECT id, position_id, scheduled_days
            FROM employees
            WHERE position_id IS NOT NULL
        """)
        existing_employees = cursor.fetchall()

        if existing_employees:
            print(f"\nMigrating {len(existing_employees)} employee position assignments...")
            migrated_count = 0

            for emp_id, pos_id, scheduled_days in existing_employees:
                # Check if already migrated
                cursor.execute("""
                    SELECT COUNT(*) FROM employee_position_schedule
                    WHERE employee_id = ? AND position_id = ?
                """, (emp_id, pos_id))

                if cursor.fetchone()[0] == 0:
                    # Parse scheduled_days (could be JSON string or None)
                    days = []
                    if scheduled_days:
                        try:
                            if isinstance(scheduled_days, str):
                                days = json.loads(scheduled_days)
                            elif isinstance(scheduled_days, list):
                                days = scheduled_days
                        except:
                            days = []

                    # Insert into new table
                    cursor.execute("""
                        INSERT INTO employee_position_schedule (employee_id, position_id, days_of_week)
                        VALUES (?, ?, ?)
                    """, (emp_id, pos_id, json.dumps(days)))
                    migrated_count += 1

            print(f"✓ Migrated {migrated_count} employee-position assignments")
        else:
            print("✓ No existing employees to migrate")

        # Step 4: Add position_id to daily_employee_entries
        cursor.execute("PRAGMA table_info(daily_employee_entries)")
        entry_columns = [row[1] for row in cursor.fetchall()]

        if 'position_id' not in entry_columns:
            print("\nAdding position_id column to daily_employee_entries table...")
            cursor.execute("ALTER TABLE daily_employee_entries ADD COLUMN position_id INTEGER")

            # Populate position_id for existing entries from employee's position
            cursor.execute("""
                UPDATE daily_employee_entries
                SET position_id = (
                    SELECT position_id FROM employees WHERE employees.id = daily_employee_entries.employee_id
                )
                WHERE position_id IS NULL
            """)
            print("✓ position_id column added and populated from employee records")
        else:
            print("✓ position_id column already exists in daily_employee_entries")

        # Step 5: Make position_id nullable in employees table
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        print("\nMaking position_id nullable in employees table...")

        # Check if position_id is already nullable by checking if we can insert NULL
        try:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='employees'")
            table_sql = cursor.fetchone()[0]

            # If position_id is NOT NULL, we need to recreate the table
            if 'position_id INTEGER NOT NULL' in table_sql or 'position_id" INTEGER NOT NULL' in table_sql:
                print("  Recreating employees table to make position_id nullable...")

                # Create temporary table with new schema
                cursor.execute("""
                    CREATE TABLE employees_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR NOT NULL,
                        first_name VARCHAR,
                        last_name VARCHAR,
                        slug VARCHAR NOT NULL UNIQUE,
                        is_active BOOLEAN DEFAULT 1,
                        position_id INTEGER,
                        scheduled_days TEXT,
                        FOREIGN KEY (position_id) REFERENCES positions(id)
                    )
                """)

                # Copy data from old table
                cursor.execute("""
                    INSERT INTO employees_new (id, name, first_name, last_name, slug, is_active, position_id, scheduled_days)
                    SELECT id, name, first_name, last_name, slug, is_active, position_id, scheduled_days
                    FROM employees
                """)

                # Drop old table and rename new one
                cursor.execute("DROP TABLE employees")
                cursor.execute("ALTER TABLE employees_new RENAME TO employees")

                print("  ✓ Employees table recreated with nullable position_id")
            else:
                print("  ✓ position_id is already nullable")
        except Exception as e:
            print(f"  Warning: Could not make position_id nullable: {e}")
            print("  Continuing anyway - new employees may fail to save until this is fixed")

        # Step 6: Verify migration
        cursor.execute("SELECT COUNT(*) FROM employee_position_schedule")
        schedule_count = cursor.fetchone()[0]
        print(f"\n✓ Total employee_position_schedule records: {schedule_count}")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNote: Old columns (position_id, scheduled_days) kept for safety.")
        print("They will not be used by the application but remain for rollback if needed.")
        return True

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """Main entry point for the migration script."""
    print("=" * 60)
    print("Multi-Position & Inactive Status Migration")
    print("=" * 60)

    if not database_exists():
        print("\n📦 Database does not exist. Creating new database with updated schema...")
        init_db()
        print("✅ Database created successfully!")
        print("\nℹ️  No migration needed - database was created with the new schema.")
    else:
        print("\n📊 Existing database found. Running migration...")
        print("-" * 60)

        try:
            migrate()
            print("-" * 60)
        except Exception as e:
            print("-" * 60)
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("  • Add multiple positions to employees")
    print("  • Set different schedules per position")
    print("  • Mark employees as inactive")
    print("  • All historical data has been preserved")
    print()

if __name__ == "__main__":
    main()
