"""
Enable Foreign Keys and Clean Up Orphaned Executions

This migration:
1. Enables foreign key constraints in SQLite (critical fix)
2. Removes any orphaned task_executions that don't have a parent scheduled_task
3. Verifies the foreign key constraint is working properly

Note: Foreign keys must be enabled on EVERY connection in SQLite.
The database.py file has been updated to do this automatically.
"""

MIGRATION_ID = "2026_02_03_enable_foreign_keys_cleanup"


def upgrade(conn, column_exists, table_exists):
    """
    Enable foreign keys and clean up orphaned task executions.

    This migration ensures data integrity by:
    - Enabling foreign key constraints (CASCADE deletes work properly)
    - Removing orphaned task_executions without parent scheduled_tasks
    """
    cursor = conn.cursor()

    # Enable foreign keys for this connection
    print("  → Enabling foreign keys for this connection...")
    cursor.execute("PRAGMA foreign_keys=ON")

    # Verify foreign keys are enabled
    cursor.execute("PRAGMA foreign_keys")
    fk_status = cursor.fetchone()[0]
    print(f"  ✓ Foreign keys status: {'ENABLED' if fk_status else 'DISABLED'}")

    if not fk_status:
        print("  ⚠ WARNING: Foreign keys could not be enabled!")

    # Check for orphaned executions
    print("  → Checking for orphaned task executions...")
    cursor.execute("""
        SELECT COUNT(*) FROM task_executions
        WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
    """)
    orphaned_count = cursor.fetchone()[0]
    print(f"  → Found {orphaned_count} orphaned execution(s)")

    if orphaned_count > 0:
        # Get details before deletion (limited to first 10)
        cursor.execute("""
            SELECT id, task_id, started_at, status
            FROM task_executions
            WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
            ORDER BY started_at DESC
            LIMIT 10
        """)
        orphaned = cursor.fetchall()

        print("  → Orphaned executions to be deleted:")
        for exec_id, task_id, started_at, status in orphaned:
            print(f"    - Execution {exec_id}: task_id={task_id}, status={status}, started={started_at}")

        if orphaned_count > 10:
            print(f"    ... and {orphaned_count - 10} more")

        # Delete orphaned executions
        print("  → Deleting orphaned task executions...")
        cursor.execute("""
            DELETE FROM task_executions
            WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
        """)
        print(f"  ✓ Deleted {orphaned_count} orphaned execution(s)")
    else:
        print("  ✓ No orphaned executions found")

    # Show summary
    cursor.execute("SELECT COUNT(*) FROM scheduled_tasks")
    task_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM task_executions")
    execution_count = cursor.fetchone()[0]

    print(f"  → Final counts: {task_count} tasks, {execution_count} executions")
    print("  ✓ Migration completed successfully")
    print("  ℹ️  Foreign keys are now enabled on every new database connection via database.py")
