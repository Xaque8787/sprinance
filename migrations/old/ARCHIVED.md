# Archived Migrations

## Notice

The migrations in this directory are **archived** and are no longer executed by the migration system.

## What Changed

As of January 2026, the migration system was refactored to use a **database-backed tracking system** instead of filesystem-based tracking.

### Old System (these files)
- ✗ Migrations tracked via filesystem
- ✗ Applied migrations moved to `/migrations/old`
- ✗ Files mutated during deployment
- ✗ Various formats and conventions

### New System
- ✓ Migrations tracked in `schema_migrations` database table
- ✓ Migration files are immutable (never moved or deleted)
- ✓ Consistent format with `MIGRATION_ID` and `upgrade()` function
- ✓ Defensive checks and idempotency built-in
- ✓ See `/migrations/README.md` for details

## Why Keep These Files?

These files are kept for:
- **Historical reference** - Understanding how the schema evolved
- **Documentation** - What changes were made and when
- **Debugging** - Tracking down when specific changes were introduced

## Current Schema

For the current database schema, see:
- **Models**: `/app/models.py` - Current target schema
- **Migrations**: `/migrations/` - Steps to reach current schema from any previous state
- **Documentation**: `/MIGRATION_SYSTEM.md` - Migration system architecture

## Do Not Execute

These files should **not** be executed directly. If you need to recreate the database:

1. Delete the database file: `rm data/database.db`
2. Restart the application: `python run.py` or restart Docker container
3. The application will create a fresh database with the current schema

## Converting to New Format

If you need to reference these migrations for creating new migrations:

1. Create a new file in `/migrations/` with format: `YYYY_MM_DD_description.py`
2. Define `MIGRATION_ID` and `upgrade()` function
3. Add defensive checks (see `/migrations/README.md`)
4. Test with existing database

Example conversion:

**Old format:**
```python
def upgrade():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN email TEXT"))
        conn.commit()
```

**New format:**
```python
MIGRATION_ID = "2026_01_28_add_user_email"

def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()
    if not column_exists('users', 'email'):
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

See `/MIGRATION_SYSTEM.md` for complete conversion guide.
