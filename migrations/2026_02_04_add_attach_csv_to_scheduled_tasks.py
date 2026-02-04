"""
Migration: Add attach_csv column to scheduled_tasks

This migration adds support for attaching CSV files to scheduled report emails.

Changes:
- Adds attach_csv BOOLEAN column to scheduled_tasks table (defaults to FALSE)
- Allows users to configure whether CSV files should be attached to report emails
- Backward compatible - existing tasks continue to work without attachments
"""

MIGRATION_ID = "2026_02_04_add_attach_csv_to_scheduled_tasks"

def upgrade(conn, column_exists, table_exists):
    """Add attach_csv column to scheduled_tasks table"""
    cursor = conn.cursor()

    if not column_exists('scheduled_tasks', 'attach_csv'):
        cursor.execute("""
            ALTER TABLE scheduled_tasks
            ADD COLUMN attach_csv BOOLEAN DEFAULT FALSE;
        """)
        print("  ✓ Added attach_csv column to scheduled_tasks table")
    else:
        print("  ⚠ attach_csv column already exists, skipping")

def downgrade(conn, column_exists, table_exists):
    """Remove attach_csv column from scheduled_tasks table"""
    cursor = conn.cursor()

    # SQLite doesn't support DROP COLUMN directly, would need to recreate table
    print("  ⚠ Downgrade not implemented (SQLite limitation)")
