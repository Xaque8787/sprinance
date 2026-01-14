#!/usr/bin/env python3
"""
Quick fix script to add tip_values column to the database.
Run this from your project directory where the .venv exists.
"""

import sqlite3
import os

# Database path
db_path = "data/database.db"

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    print("Make sure you're running this from the project root directory.")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(daily_employee_entries)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'tip_values' in columns:
        print("✓ Column 'tip_values' already exists!")
    else:
        print("Adding 'tip_values' column...")
        cursor.execute("ALTER TABLE daily_employee_entries ADD COLUMN tip_values TEXT DEFAULT '{}'")
        conn.commit()
        print("✓ Column 'tip_values' added successfully!")

    conn.close()
    print("\nDatabase migration completed. You can now restart your application.")

except sqlite3.Error as e:
    print(f"✗ Database error: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)
