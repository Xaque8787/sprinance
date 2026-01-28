# Migration System Refactoring

## Overview

This document describes the migration from the old filesystem-based migration system to the new database-backed migration system.

## What Changed

### Old System (Before)

- ✗ Migrations tracked via filesystem
- ✗ Applied migrations moved to `/migrations/old`
- ✗ Files mutated during deployment
- ✗ No idempotency guarantees
- ✗ Difficult to verify migration state

### New System (After)

- ✓ Migrations tracked in `schema_migrations` database table
- ✓ Migration files are **immutable** (never moved or deleted)
- ✓ Safe to run repeatedly (idempotent)
- ✓ Defensive checks in each migration
- ✓ Transactional execution
- ✓ Easy to audit migration history (`SELECT * FROM schema_migrations`)

## Architecture

### Database Tracking

```sql
CREATE TABLE schema_migrations (
    id TEXT PRIMARY KEY,              -- e.g., "2026_01_28_add_email_field"
    applied_at TIMESTAMP NOT NULL     -- When migration was applied
);
```

### Migration File Structure

Each migration file must define:

```python
# Unique, sortable identifier
MIGRATION_ID = "2026_01_28_description"

# Function that applies the migration
def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()
    # ... migration logic
```

### Runner Behavior

1. Connect to database
2. Ensure `schema_migrations` table exists
3. Load all migration files from `/migrations`
4. Sort by `MIGRATION_ID`
5. For each migration:
   - Check if already in `schema_migrations`
   - If not: apply in transaction, record success
   - If yes: skip

## Migration File Format Comparison

### Old Format

```python
"""Migration description"""
from app.database import engine
from sqlalchemy import text

def upgrade():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN email TEXT"))
        conn.commit()

if __name__ == "__main__":
    upgrade()
```

### New Format

```python
"""Migration description"""

MIGRATION_ID = "2026_01_28_add_user_email"

def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()

    # Defensive check
    if not column_exists('users', 'email'):
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        print("  ✓ Added email column")
    else:
        print("  ℹ️  email column already exists, skipping")
```

## Converting Old Migrations

If you need to convert an old migration to the new format:

### Step 1: Define MIGRATION_ID

Choose a unique, sortable ID based on the date or sequence:

```python
MIGRATION_ID = "2026_01_28_add_employee_snapshots"
```

### Step 2: Update function signature

Change from:
```python
def upgrade():
    with engine.connect() as conn:
```

To:
```python
def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()
```

### Step 3: Add defensive checks

Before:
```python
cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

After:
```python
if not column_exists('users', 'email'):
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

### Step 4: Remove manual commits

The runner handles transactions automatically:

Before:
```python
conn.commit()
```

After:
```python
# No manual commit needed - runner handles it
```

## Helper Functions

The migration runner provides helper functions:

### column_exists(table_name, column_name)

```python
if not column_exists('employees', 'is_active'):
    cursor.execute("ALTER TABLE employees ADD COLUMN is_active BOOLEAN DEFAULT 1")
```

### table_exists(table_name)

```python
if not table_exists('audit_log'):
    cursor.execute("""
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY,
            action TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

## Best Practices

### 1. Always Use Defensive Checks

Every migration should check before acting:

```python
# ✅ Good - idempotent
if not column_exists('users', 'email'):
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")

# ❌ Bad - fails on second run
cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

### 2. Use Descriptive IDs

```python
# ✅ Good - clear and sortable
MIGRATION_ID = "2026_01_28_add_employee_snapshots"

# ❌ Bad - ambiguous
MIGRATION_ID = "migration_1"
```

### 3. Document Your Changes

```python
"""
Add employee snapshot fields for historical data preservation

This migration adds snapshot columns that preserve employee and
position names even after deletion, ensuring report accuracy.
"""
```

### 4. Handle Data Carefully

```python
# Populate snapshots for existing records
cursor.execute("""
    UPDATE daily_employee_entries
    SET employee_name_snapshot = (
        SELECT name FROM employees
        WHERE employees.id = daily_employee_entries.employee_id
    )
    WHERE employee_id IS NOT NULL
      AND employee_name_snapshot IS NULL  -- Don't overwrite existing
""")
```

### 5. Test Locally First

Always test migrations on a copy of your database before deploying.

## Deployment Workflow

### Development

1. Create migration file: `/migrations/YYYY_MM_DD_description.py`
2. Define `MIGRATION_ID` and `upgrade()` function
3. Add defensive checks
4. Test locally

### Testing

```bash
# Run migrations
python run_migrations.py

# Verify in database
sqlite3 data/database.db "SELECT * FROM schema_migrations;"
```

### Deployment

1. Build Docker image (includes new migration)
2. Deploy container
3. Container startup runs `run_migrations.py` automatically
4. Migration applied and recorded
5. Application starts with updated schema

## Troubleshooting

### "Migration already applied" but change not present

This can happen if:
- Migration was recorded but not committed
- Database was manually modified
- Migration had a bug

Solution: Create a new migration with the needed changes.

### Migration fails mid-execution

- Transaction automatically rolls back
- Fix migration file
- Restart container
- Migration will retry

### Need to skip a migration

You can manually insert into `schema_migrations`:

```sql
INSERT INTO schema_migrations (id, applied_at)
VALUES ('2026_01_28_problematic_migration', CURRENT_TIMESTAMP);
```

Only do this if you've manually applied the changes.

### Want to re-run a migration

1. Remove from `schema_migrations`:
   ```sql
   DELETE FROM schema_migrations WHERE id = '2026_01_28_migration_name';
   ```
2. Restart application or run `python run_migrations.py`

**Warning**: Only do this if the migration is idempotent!

## Directory Structure

```
project/
├── migrations/                          # Migration files (immutable)
│   ├── README.md                       # Migration documentation
│   ├── example_*.py.example            # Example templates
│   └── 2026_01_28_some_change.py      # Actual migrations
├── migrations/old/                      # Old migrations (archived)
│   └── *.py                            # No longer executed
├── run_migrations.py                   # New migration runner
├── app/
│   ├── models.py                       # SQLAlchemy models (target schema)
│   └── database.py                     # Database connection
└── data/
    └── database.db                     # SQLite database
```

## FAQ

### Do I need to update models.py?

Yes! Your models should always reflect the **final, desired schema**. Migrations bridge the gap from old schema to new.

### What about fresh databases?

Fresh databases:
1. `init_db()` creates base schema from models
2. Migration runner applies any additional migrations
3. Final schema matches models + migrations

### Can I delete old migrations?

**No.** Migration files should remain forever. They serve as documentation and ensure consistent schema across all deployments.

### What if I made a mistake in a migration?

Create a new migration to fix it. Don't modify the original migration.

### How do I see migration history?

```sql
SELECT id, applied_at
FROM schema_migrations
ORDER BY applied_at;
```

### Are migrations reversible?

Not by default. If you need reversibility, you can add a `downgrade()` function, but it's not currently used by the runner.

## Migration Checklist

When creating a new migration:

- [ ] Unique `MIGRATION_ID` in `YYYY_MM_DD_description` format
- [ ] `upgrade(conn, column_exists, table_exists)` function defined
- [ ] Defensive checks before schema changes
- [ ] Docstring explaining what and why
- [ ] Tested locally with existing database
- [ ] Tested with fresh database
- [ ] Committed to version control

## Summary

The new migration system is:
- **Safer**: Transactions + defensive checks
- **Clearer**: Database tracking + immutable files
- **Simpler**: No filesystem mutations
- **Better**: Idempotent + self-documenting

All future migrations should follow the new format described in `/migrations/README.md`.
