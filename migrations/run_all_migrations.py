#!/usr/bin/env python3
"""
Helper script to run all database migrations in the correct order.

Usage:
    python3 migrations/run_all_migrations.py

Or from the migrations directory:
    python3 run_all_migrations.py
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import migration modules
import migrate_database
import migrate_to_crud_system
import add_crud_financial_items_migration
import remove_old_fields_migration
import add_tip_out_field

def run_all_migrations():
    """Run all migrations in the correct order."""
    migrations = [
        ("Initial Database Setup", migrate_database.migrate),
        ("CRUD System Migration", migrate_to_crud_system.migrate),
        ("CRUD Financial Items", add_crud_financial_items_migration.migrate),
        ("Remove Old Fields", remove_old_fields_migration.migrate),
        ("Add Tip Out Field", add_tip_out_field.migrate),
    ]

    print("=" * 60)
    print("Running All Database Migrations")
    print("=" * 60)
    print()

    for i, (name, migration_func) in enumerate(migrations, 1):
        print(f"[{i}/{len(migrations)}] Running: {name}")
        print("-" * 60)
        try:
            migration_func()
            print()
        except Exception as e:
            print(f"ERROR: Migration failed: {e}")
            print("Stopping migration process.")
            sys.exit(1)

    print("=" * 60)
    print("All migrations completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_migrations()
