"""
Migration: Add scheduled checks and EFTs tables

This migration adds support for scheduling checks and EFTs to auto-populate
on the daily balance form based on days of the week.

Tables Added:
- scheduled_checks: Stores check configurations with day-of-week scheduling
  - id: Primary key
  - check_number: Default check number (can be edited on daily form)
  - payable_to: Default payee name
  - default_total: Default amount (can be edited on daily form)
  - days_of_week: JSON array of scheduled days (e.g., ["Monday", "Friday"])
  - memo: Default memo text (optional)
  - is_active: Whether this scheduled check is active

- scheduled_efts: Stores EFT configurations with day-of-week scheduling
  - id: Primary key
  - card_number: Default card number
  - payable_to: Default payee name
  - default_total: Default amount (can be edited on daily form)
  - days_of_week: JSON array of scheduled days (e.g., ["Monday", "Friday"])
  - memo: Default memo text (optional)
  - is_active: Whether this scheduled EFT is active

Purpose:
Similar to how employees auto-populate based on their scheduled days,
checks and EFTs will now auto-populate on the daily balance form when
the selected date matches their scheduled days of the week.
"""

MIGRATION_ID = "2026_01_31_add_scheduled_checks_efts"

def upgrade(conn, column_exists, table_exists):
    """Create scheduled_checks and scheduled_efts tables"""
    cursor = conn.cursor()

    if not table_exists('scheduled_checks'):
        cursor.execute("""
            CREATE TABLE scheduled_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_number TEXT,
                payable_to TEXT NOT NULL,
                default_total REAL DEFAULT 0.0,
                days_of_week TEXT DEFAULT '[]',
                memo TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created scheduled_checks table")
    else:
        print("  ℹ️  scheduled_checks table already exists, skipping")

    if not table_exists('scheduled_efts'):
        cursor.execute("""
            CREATE TABLE scheduled_efts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_number TEXT,
                payable_to TEXT NOT NULL,
                default_total REAL DEFAULT 0.0,
                days_of_week TEXT DEFAULT '[]',
                memo TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created scheduled_efts table")
    else:
        print("  ℹ️  scheduled_efts table already exists, skipping")
