"""
Migration: Add log rotation and level settings

This migration adds default settings for log file rotation and level management.

Settings Added:
- log_max_size_mb: Maximum size of log file in MB before rotation (default: 10)
- log_backup_count: Number of rotated log files to keep (default: 5)
- log_capture_info: Capture INFO level logs (default: 0/disabled)
- log_capture_debug: Capture DEBUG level logs (default: 0/disabled)

Purpose:
Allows administrators to configure how error logs are rotated to prevent
disk space issues while maintaining historical error data for troubleshooting.
Also enables control over log verbosity levels.
"""

MIGRATION_ID = "2026_02_01_add_log_settings"

def upgrade(conn, column_exists, table_exists):
    """Add default log rotation settings"""
    cursor = conn.cursor()

    # Create settings table if it doesn't exist
    if not table_exists('settings'):
        cursor.execute("""
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)")
        print("  ✓ Created settings table")

    # Check if settings already exist
    cursor.execute("""
        SELECT key FROM settings
        WHERE key IN ('log_max_size_mb', 'log_backup_count', 'log_capture_info', 'log_capture_debug')
    """)
    existing_settings = {row[0] for row in cursor.fetchall()}

    settings_to_add = [
        ('log_max_size_mb', '10', 'Maximum size of log file in MB before rotation'),
        ('log_backup_count', '5', 'Number of rotated log files to keep'),
        ('log_capture_info', '0', 'Capture INFO level logs'),
        ('log_capture_debug', '0', 'Capture DEBUG level logs'),
    ]

    for key, value, description in settings_to_add:
        if key not in existing_settings:
            cursor.execute("""
                INSERT INTO settings (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
            print(f"  ✓ Added {key} setting")
        else:
            print(f"  ℹ️  {key} setting already exists, skipping")
