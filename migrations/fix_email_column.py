#!/usr/bin/env python3
"""
Direct migration to add email column to users table.
Run this from your project directory: python3 fix_email_column.py
"""

import sqlite3
import os
import sys

def add_email_column():
    db_path = "data/database.db"

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print(f"Current directory: {os.getcwd()}")
        print("\nPlease run this script from your project root directory:")
        print("  cd /home/spiros-zach/Projects/sprinance")
        print("  python3 fix_email_column.py")
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table not found in database")
            conn.close()
            sys.exit(1)

        # Check current schema
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"Current columns in users table: {', '.join(column_names)}")

        if 'email' in column_names:
            print("✓ Email column already exists")
        else:
            print("Adding email column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR")
            conn.commit()
            print("✓ Successfully added email column to users table")

        # Verify the change
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated columns: {', '.join(new_columns)}")

        conn.close()
        print("\n✓ Migration complete!")

    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    add_email_column()
