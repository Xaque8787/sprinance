#!/usr/bin/env python3
"""
Migration runner that executes all migration files in the migrations directory
and moves them to migrations/old after successful execution.

This allows for automated database updates when deploying new versions.
"""
import os
import sys
import shutil
from pathlib import Path

def run_migrations():
    """Run all migration scripts found in the migrations directory."""
    # Support both Docker (/app) and local paths
    if os.path.exists("/app/migrations"):
        migrations_dir = Path("/app/migrations")
    else:
        migrations_dir = Path(__file__).parent / "migrations"

    old_migrations_dir = migrations_dir / "old"

    # Ensure the old migrations directory exists
    old_migrations_dir.mkdir(exist_ok=True)

    # Find all Python migration files (exclude __init__.py and __pycache__)
    migration_files = sorted([
        f for f in migrations_dir.glob("*.py")
        if f.name != "__init__.py"
    ])

    if not migration_files:
        print("No migration files found. Skipping migration step.")
        return True

    print(f"Found {len(migration_files)} migration file(s) to run:")
    for migration_file in migration_files:
        print(f"  - {migration_file.name}")
    print()

    # Run each migration
    for migration_file in migration_files:
        try:
            print(f"Running migration: {migration_file.name}")

            # Execute the migration file
            with open(migration_file) as f:
                migration_code = f.read()

            # Execute in a namespace with access to app modules
            exec_globals = {
                '__name__': '__main__',
                '__file__': str(migration_file),
            }
            exec(migration_code, exec_globals)

            print(f"✓ Successfully executed: {migration_file.name}")

            # Move the migration file to old directory
            destination = old_migrations_dir / migration_file.name

            # If file already exists in old, add a timestamp
            if destination.exists():
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = destination.stem
                suffix = destination.suffix
                destination = old_migrations_dir / f"{stem}_{timestamp}{suffix}"

            shutil.move(str(migration_file), str(destination))
            print(f"✓ Moved to: migrations/old/{destination.name}")
            print()

        except Exception as e:
            print(f"✗ Error running migration {migration_file.name}:", file=sys.stderr)
            print(f"  {str(e)}", file=sys.stderr)
            print("\nMigration failed. Not moving file to old directory.", file=sys.stderr)
            return False

    print(f"All migrations completed successfully!")
    return True

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
