#!/usr/bin/env python3

import sqlite3
import os

db_path = "data/database.db"

if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
    print("The migration will be applied automatically when the database is created.")
    exit(0)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("Users table doesn't exist yet - skipping migration (will be created automatically)")
        conn.close()
        exit(0)

    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'email' in columns:
        print("Email column already exists in users table")
    else:
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR")
        conn.commit()
        print("Successfully added email column to users table")

    conn.close()
except Exception as e:
    print(f"Error during migration: {str(e)}")
    raise
