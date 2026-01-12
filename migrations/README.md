# Database Migrations

This directory contains database migration scripts that are automatically executed when the Docker container starts.

## How It Works

1. **On Container Startup**: The `docker-entrypoint.sh` script always runs `run_migrations.py`
2. **Migration Execution**: Any `.py` files in this directory are executed in alphabetical order
3. **Archive**: After successful execution, migration files are moved to `migrations/old/`
4. **Empty Directory**: If no migration files exist, the migration step is gracefully skipped

## Adding New Migrations

To add a database migration for a future update:

1. Create a Python migration file in this directory
2. Name it descriptively with a date prefix (e.g., `20260112_add_new_column.py`)
3. The migration file should contain the necessary database modification code
4. Include the migration file when building a new Docker image
5. When users pull and run the new image, the migration will automatically execute

## Migration File Example

```python
#!/usr/bin/env python3
"""
Migration: Add description column to employees table
Date: 2026-01-12
"""
import sqlite3

def run_migration():
    conn = sqlite3.connect('/app/data/database.db')
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(employees)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'description' not in columns:
            cursor.execute("""
                ALTER TABLE employees
                ADD COLUMN description TEXT
            """)
            conn.commit()
            print("✓ Added description column to employees table")
        else:
            print("⚠ description column already exists, skipping")

    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
```

## Best Practices

- Always check if the change already exists before applying it (idempotent migrations)
- Use descriptive file names with dates
- Include error handling
- Test migrations before deploying
- Keep migrations focused on a single change

## Archived Migrations

Successfully executed migrations are stored in `migrations/old/` for reference.
