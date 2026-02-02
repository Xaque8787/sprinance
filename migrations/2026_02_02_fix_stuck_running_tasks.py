"""
Migration: Fix stuck running task executions

This migration updates all task executions that are stuck in 'running' state
to mark them as 'completed'. This fixes historical records where the started_at
timestamp was not properly set and the status was never updated after completion.
"""

MIGRATION_ID = "2026_02_02_fix_stuck_running_tasks"

def upgrade(conn, column_exists, table_exists):
    """
    Update all task executions stuck in 'running' state to 'completed'.
    Sets completed_at to started_at if available, or CURRENT_TIMESTAMP otherwise.
    """
    cursor = conn.cursor()

    # Check if task_executions table exists
    if not table_exists('task_executions'):
        print("  ℹ️  task_executions table doesn't exist, skipping")
        return

    # Count how many stuck executions exist
    cursor.execute("SELECT COUNT(*) FROM task_executions WHERE status = 'running'")
    count = cursor.fetchone()[0]

    if count == 0:
        print("  ℹ️  No stuck task executions found")
        return

    # Update executions that are stuck in 'running' state
    cursor.execute("""
        UPDATE task_executions
        SET status = 'completed',
            completed_at = COALESCE(started_at, CURRENT_TIMESTAMP)
        WHERE status = 'running'
    """)

    print(f"  ✓ Updated {count} stuck task execution(s) from 'running' to 'completed'")
