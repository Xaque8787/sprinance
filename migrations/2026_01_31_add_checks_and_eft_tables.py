"""
# Add Checks and EFT Transaction Tables

## Overview
This migration adds comprehensive support for tracking check and EFT (Electronic Funds Transfer)
transactions in daily balance reports.

## Changes Made

### 1. New Tables

#### `check_payees`
Stores reusable payee names for checks:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `name` (TEXT, UNIQUE, NOT NULL): Payee name
- `created_at` (TEXT): Timestamp when created

#### `eft_card_numbers`
Stores reusable card numbers for EFT transactions:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `number` (TEXT, UNIQUE, NOT NULL): Card number
- `created_at` (TEXT): Timestamp when created

#### `eft_payees`
Stores reusable payee names for EFT transactions (separate from check payees):
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `name` (TEXT, UNIQUE, NOT NULL): Payee name
- `created_at` (TEXT): Timestamp when created

#### `daily_balance_checks`
Stores check transactions for daily balance reports:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `daily_balance_id` (INTEGER, FOREIGN KEY): References daily_balance.id
- `check_number` (TEXT): Check number entered by user
- `date` (TEXT, NOT NULL): Date of the check
- `payable_to` (TEXT, NOT NULL): Who the check is made out to
- `total` (REAL, NOT NULL): Check amount
- `memo` (TEXT): Optional memo/note

#### `daily_balance_efts`
Stores EFT transactions for daily balance reports:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `daily_balance_id` (INTEGER, FOREIGN KEY): References daily_balance.id
- `date` (TEXT, NOT NULL): Date of the EFT
- `card_number` (TEXT): Card number used
- `payable_to` (TEXT, NOT NULL): Payee name
- `total` (REAL, NOT NULL): Transaction amount
- `memo` (TEXT): Optional memo/note

### 2. Security & Data Integrity

- All check and EFT records cascade delete when the parent daily_balance is deleted
- Foreign key constraints ensure referential integrity
- Unique constraints on reusable values prevent duplicates

### 3. Important Notes

- Check payees and EFT payees are stored separately to allow different lists
- EFT card numbers and EFT payees are also separate lists
- Dates are auto-populated from the daily balance date but stored separately for flexibility
- All monetary values use REAL (float) type for decimal precision
"""

MIGRATION_ID = "2026_01_31_add_checks_and_eft_tables"


def upgrade(conn, column_exists, table_exists):
    """Create checks and EFT related tables"""
    cursor = conn.cursor()

    if not table_exists('check_payees'):
        cursor.execute("""
            CREATE TABLE check_payees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created check_payees table")
    else:
        print("  ℹ️  check_payees table already exists, skipping")

    if not table_exists('eft_card_numbers'):
        cursor.execute("""
            CREATE TABLE eft_card_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created eft_card_numbers table")
    else:
        print("  ℹ️  eft_card_numbers table already exists, skipping")

    if not table_exists('eft_payees'):
        cursor.execute("""
            CREATE TABLE eft_payees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created eft_payees table")
    else:
        print("  ℹ️  eft_payees table already exists, skipping")

    if not table_exists('daily_balance_checks'):
        cursor.execute("""
            CREATE TABLE daily_balance_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_balance_id INTEGER NOT NULL,
                check_number TEXT,
                date TEXT NOT NULL,
                payable_to TEXT NOT NULL,
                total REAL NOT NULL,
                memo TEXT,
                FOREIGN KEY (daily_balance_id) REFERENCES daily_balance(id) ON DELETE CASCADE
            )
        """)
        print("  ✓ Created daily_balance_checks table")
    else:
        print("  ℹ️  daily_balance_checks table already exists, skipping")

    if not table_exists('daily_balance_efts'):
        cursor.execute("""
            CREATE TABLE daily_balance_efts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_balance_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                card_number TEXT,
                payable_to TEXT NOT NULL,
                total REAL NOT NULL,
                memo TEXT,
                FOREIGN KEY (daily_balance_id) REFERENCES daily_balance(id) ON DELETE CASCADE
            )
        """)
        print("  ✓ Created daily_balance_efts table")
    else:
        print("  ℹ️  daily_balance_efts table already exists, skipping")
