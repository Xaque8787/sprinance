import sqlite3
import os
import json

def migrate():
    """
    Migration: Add multi-position support and inactive status for employees

    Changes:
    1. Add is_active column to employees table (default TRUE)
    2. Create employee_position_schedule table for multi-position support
    3. Migrate existing data (employee.position_id + scheduled_days → employee_position_schedule)
    4. Keep old columns for safety (position_id, scheduled_days remain but won't be used)

    Historical data preservation:
    - All existing daily_balance_entry records remain untouched
    - Old employee.position_id and scheduled_days columns kept for rollback safety
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    if not os.path.exists(db_path):
        print("Database does not exist. Will be created with new schema.")
        return

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

        # Step 5: Verify migration
        cursor.execute("SELECT COUNT(*) FROM employee_position_schedule")
        schedule_count = cursor.fetchone()[0]
        print(f"\n✓ Total employee_position_schedule records: {schedule_count}")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNote: Old columns (position_id, scheduled_days) kept for safety.")
        print("They will not be used by the application but remain for rollback if needed.")

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
