#!/usr/bin/env python3
"""
Database-backed migration runner.

This runner:
- Tracks applied migrations in the `schema_migrations` table
- Keeps migration files immutable (never moves or deletes them)
- Runs migrations in transaction with redundant safety checks
- Is safe to run repeatedly (idempotent)

Each migration file must define:
- MIGRATION_ID: A unique, sortable identifier (e.g., "2026_01_28_add_settings_table")
- upgrade(conn): Function that applies the migration
"""
import os
import sys
import sqlite3
import importlib.util
from pathlib import Path
from datetime import datetime, timezone


def get_migrations_dir():
    """Get the migrations directory path."""
    if os.path.exists("/app/migrations"):
        return Path("/app/migrations")
    return Path(__file__).parent / "migrations"


def get_database_path():
    """Get the database file path."""
    if os.path.exists("/app/data"):
        return "/app/data/database.db"
    return str(Path(__file__).parent / "data" / "database.db")


def ensure_schema_migrations_table(conn):
    """Create the schema_migrations table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id TEXT PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("✓ schema_migrations table ready")


def get_applied_migrations(conn):
    """Return a set of migration IDs that have already been applied."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM schema_migrations ORDER BY id")
    return {row[0] for row in cursor.fetchall()}


def load_migration_module(migration_file):
    """Load a migration file as a Python module."""
    spec = importlib.util.spec_from_file_location(
        migration_file.stem,
        migration_file
    )
    module = importlib.util.module_from_spec(spec)

    # Make app modules available to migrations
    sys.path.insert(0, str(Path(__file__).parent))

    spec.loader.exec_module(module)
    return module


def discover_migrations(migrations_dir):
    """
    Discover all migration files and return them sorted by MIGRATION_ID.

    Returns:
        List of tuples: (migration_id, file_path, module)
    """
    migrations = []

    # Find all Python files (exclude __init__.py and __pycache__)
    migration_files = sorted([
        f for f in migrations_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    ])

    for migration_file in migration_files:
        try:
            module = load_migration_module(migration_file)

            # Check if module has required attributes
            if not hasattr(module, 'MIGRATION_ID'):
                print(f"⚠️  Skipping {migration_file.name}: No MIGRATION_ID defined")
                continue

            if not hasattr(module, 'upgrade'):
                print(f"⚠️  Skipping {migration_file.name}: No upgrade() function defined")
                continue

            migration_id = module.MIGRATION_ID
            migrations.append((migration_id, migration_file, module))

        except Exception as e:
            print(f"⚠️  Error loading {migration_file.name}: {e}")
            continue

    # Sort by MIGRATION_ID to ensure consistent ordering
    migrations.sort(key=lambda x: x[0])

    return migrations


def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table (SQLite helper)."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def run_migrations():
    """
    Main migration runner.

    1. Ensures database and schema_migrations table exist
    2. Discovers all migration files
    3. Applies unapplied migrations in order
    4. Records successful migrations in schema_migrations
    """
    db_path = get_database_path()
    migrations_dir = get_migrations_dir()

    print("=" * 70)
    print("Database Migration Runner")
    print("=" * 70)
    print(f"Database: {db_path}")
    print(f"Migrations directory: {migrations_dir}")
    print()

    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(db_path)

    try:
        # Ensure schema_migrations table exists
        ensure_schema_migrations_table(conn)

        # Get already-applied migrations
        applied = get_applied_migrations(conn)
        if applied:
            print(f"✓ Found {len(applied)} previously applied migration(s)")

        # Discover all migrations
        migrations = discover_migrations(migrations_dir)

        if not migrations:
            print("ℹ️  No migration files found")
            print("=" * 70)
            return True

        print(f"✓ Discovered {len(migrations)} migration file(s)")
        print()

        # Filter to only unapplied migrations
        pending = [
            (mid, mfile, mmod) for mid, mfile, mmod in migrations
            if mid not in applied
        ]

        if not pending:
            print("✅ All migrations already applied. Database is up to date.")
            print("=" * 70)
            return True

        print(f"📋 {len(pending)} migration(s) to apply:")
        for mid, mfile, _ in pending:
            print(f"   • {mid} ({mfile.name})")
        print()

        # Apply each pending migration
        for migration_id, migration_file, module in pending:
            print(f"▶️  Applying: {migration_id}")
            print(f"   File: {migration_file.name}")

            try:
                # Begin transaction
                conn.execute("BEGIN")

                # Inject helper functions into the upgrade function's context
                # This allows migrations to use column_exists(), table_exists(), etc.
                upgrade_kwargs = {
                    'column_exists': lambda table, column: column_exists(conn, table, column),
                    'table_exists': lambda table: table_exists(conn, table),
                }

                # Call the migration's upgrade function
                # Pass connection and helpers
                module.upgrade(conn, **upgrade_kwargs)

                # Record migration as applied
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO schema_migrations (id, applied_at) VALUES (?, ?)",
                    (migration_id, datetime.now(timezone.utc).isoformat())
                )

                # Commit transaction
                conn.commit()

                print(f"   ✅ Success")
                print()

            except Exception as e:
                # Rollback on error
                conn.rollback()
                print(f"   ❌ FAILED: {e}")
                print()
                print("=" * 70)
                print("Migration failed. Stopping.")
                print("=" * 70)
                return False

        print("=" * 70)
        print("✅ All migrations applied successfully!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Migration runner error: {e}", file=sys.stderr)
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
