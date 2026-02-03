"""
Enable Foreign Keys and Clean Up Orphaned Executions

This migration:
1. Enables foreign key constraints in SQLite (critical fix)
2. Removes any orphaned task_executions that don't have a parent scheduled_task
3. Verifies the foreign key constraint is working properly

Note: Foreign keys must be enabled on EVERY connection in SQLite.
The database.py file has been updated to do this automatically.
"""

import sqlite3
import os
from datetime import datetime

def get_db_path():
    """Get the database path"""
    return os.path.join("data", "database.db")

def run_migration():
    """Run the migration"""
    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False

    print(f"\n{'='*80}")
    print(f"MIGRATION: Enable Foreign Keys and Clean Up Orphaned Executions")
    print(f"Started at: {datetime.now()}")
    print(f"{'='*80}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Enable foreign keys for this connection
        print("→ Enabling foreign keys for this connection...")
        cursor.execute("PRAGMA foreign_keys=ON")

        # Verify foreign keys are enabled
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]
        print(f"  ✓ Foreign keys status: {'ENABLED' if fk_status else 'DISABLED'}")

        if not fk_status:
            print("  ⚠ WARNING: Foreign keys could not be enabled!")

        # Check for orphaned executions
        print("\n→ Checking for orphaned task executions...")
        cursor.execute("""
            SELECT COUNT(*) FROM task_executions
            WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
        """)
        orphaned_count = cursor.fetchone()[0]
        print(f"  → Found {orphaned_count} orphaned execution(s)")

        if orphaned_count > 0:
            # Get details before deletion
            cursor.execute("""
                SELECT id, task_id, started_at, status
                FROM task_executions
                WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
                ORDER BY started_at DESC
            """)
            orphaned = cursor.fetchall()

            print("\n  Orphaned executions to be deleted:")
            for exec_id, task_id, started_at, status in orphaned[:10]:  # Show first 10
                print(f"    - Execution {exec_id}: task_id={task_id}, status={status}, started={started_at}")

            if len(orphaned) > 10:
                print(f"    ... and {len(orphaned) - 10} more")

            # Delete orphaned executions
            print("\n→ Deleting orphaned task executions...")
            cursor.execute("""
                DELETE FROM task_executions
                WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
            """)
            deleted = cursor.rowcount
            print(f"  ✓ Deleted {deleted} orphaned execution(s)")

        # Commit the changes
        conn.commit()
        print("\n→ Changes committed successfully")

        # Verify cleanup
        cursor.execute("""
            SELECT COUNT(*) FROM task_executions
            WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
        """)
        remaining_orphaned = cursor.fetchone()[0]

        if remaining_orphaned == 0:
            print("  ✓ All orphaned executions cleaned up")
        else:
            print(f"  ⚠ WARNING: {remaining_orphaned} orphaned execution(s) still remain")

        # Show summary
        cursor.execute("SELECT COUNT(*) FROM scheduled_tasks")
        task_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM task_executions")
        execution_count = cursor.fetchone()[0]

        print(f"\n{'='*80}")
        print("MIGRATION SUMMARY")
        print(f"{'='*80}")
        print(f"  Scheduled Tasks: {task_count}")
        print(f"  Task Executions: {execution_count}")
        print(f"  Orphaned Cleaned: {orphaned_count}")
        print(f"  Foreign Keys: {'ENABLED' if fk_status else 'DISABLED'}")
        print(f"{'='*80}\n")

        print("✓ Migration completed successfully")
        print("\nIMPORTANT: Foreign keys are now enabled on every new database connection.")
        print("This means CASCADE deletes will work properly going forward.\n")

        return True

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
