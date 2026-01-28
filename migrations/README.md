# Database Migrations

This directory contains database migration files that are automatically applied when the application starts.

## Migration System Overview

This project uses a **database-backed migration system** that:

- Tracks applied migrations in the `schema_migrations` table
- Keeps migration files **immutable** (never moved or deleted)
- Runs migrations in **transactions** with redundant safety checks
- Is **idempotent** (safe to run repeatedly)
- Requires no manual intervention when deploying updates

## Migration File Format

Each migration file must define two things:

### 1. MIGRATION_ID

A unique, sortable identifier. Use the format: `YYYY_MM_DD_description`

```python
MIGRATION_ID = "2026_01_28_add_user_email_field"
```

### 2. upgrade() function

A function that receives a database connection and applies the migration:

```python
def upgrade(conn, column_exists, table_exists):
    """
    Apply the migration.

    Args:
        conn: SQLite database connection
        column_exists: Helper function - column_exists(table_name, column_name)
        table_exists: Helper function - table_exists(table_name)
    """
    cursor = conn.cursor()

    # Your migration logic here
    if not column_exists('users', 'email'):
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

## Complete Example

```python
"""
Add email field to users table

This migration adds an optional email field to the users table
to support email notifications and password reset functionality.
"""

MIGRATION_ID = "2026_01_28_add_user_email"

def upgrade(conn, column_exists, table_exists):
    """Add email column to users table."""
    cursor = conn.cursor()

    # Defensive check: only add if column doesn't exist
    if not column_exists('users', 'email'):
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN email TEXT
        """)
        print("  ✓ Added email column to users table")
    else:
        print("  ℹ️  email column already exists, skipping")
```

## Best Practices

### 1. Use Defensive Checks

Always check if changes are needed before applying them:

```python
# Before adding a column
if not column_exists('employees', 'is_active'):
    cursor.execute("ALTER TABLE employees ADD COLUMN is_active BOOLEAN DEFAULT 1")

# Before creating a table
if not table_exists('new_table'):
    cursor.execute("CREATE TABLE new_table (...)")
```

### 2. Use Descriptive Migration IDs

Good:
- `2026_01_28_add_employee_snapshots`
- `2026_02_15_create_audit_log_table`
- `2026_03_01_migrate_legacy_tip_data`

Bad:
- `migration_1`
- `update`
- `fix_database`

### 3. Include Documentation

Add a docstring explaining what the migration does and why:

```python
"""
Add employee snapshot fields for safe deletion

This migration adds snapshot fields that preserve employee and position
names in historical records even after the related employee or position
is deleted. This ensures reports remain accurate and complete.

Changes:
- Add employee_name_snapshot to daily_employee_entries
- Add position_name_snapshot to daily_employee_entries
- Add employee_name_snapshot to daily_financial_line_items
- Populate snapshots from current data
"""
```

### 4. Handle Data Migration Carefully

When migrating data, consider:

- Large datasets (batch updates if needed)
- NULL values
- Data validation
- Backwards compatibility

```python
# Populate snapshot data for existing records
cursor.execute("""
    UPDATE daily_employee_entries
    SET employee_name_snapshot = (
        SELECT name FROM employees
        WHERE employees.id = daily_employee_entries.employee_id
    )
    WHERE employee_id IS NOT NULL
      AND employee_name_snapshot IS NULL
""")
```

### 5. Test Idempotency

Your migration should be safe to run multiple times:

```python
# ✅ Good - checks before acting
if not column_exists('users', 'email'):
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")

# ❌ Bad - will fail on second run
cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

## SQLite-Specific Notes

### Adding Columns

SQLite's `ALTER TABLE` is limited. You can:
- Add columns (with `ADD COLUMN`)
- Rename tables (with `RENAME TO`)

You **cannot**:
- Drop columns (must recreate table)
- Modify column types (must recreate table)
- Add constraints to existing columns (must recreate table)

### Recreating Tables

When you need to modify a column's type or constraints:

```python
# Create new table with updated schema
cursor.execute("""
    CREATE TABLE employees_new (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        position_id INTEGER  -- Changed from NOT NULL to nullable
    )
""")

# Copy data
cursor.execute("""
    INSERT INTO employees_new
    SELECT id, name, position_id
    FROM employees
""")

# Replace old table
cursor.execute("DROP TABLE employees")
cursor.execute("ALTER TABLE employees_new RENAME TO employees")
```

### Checking Schema

Use PRAGMA commands to inspect the current schema:

```python
# Get table columns
cursor.execute("PRAGMA table_info(employees)")
columns = [row[1] for row in cursor.fetchall()]

# Get table definition
cursor.execute("""
    SELECT sql FROM sqlite_master
    WHERE type='table' AND name='employees'
""")
table_sql = cursor.fetchone()[0]
```

## Migration Lifecycle

1. **Development**: Create migration file in `/migrations`
2. **Testing**: Test locally with existing database
3. **Deployment**: Build Docker image with new migration
4. **Automatic**: Container runs `run_migrations.py` on startup
5. **Recording**: Migration recorded in `schema_migrations` table
6. **Persistence**: Migration file stays in `/migrations` forever

## Troubleshooting

### Migration fails mid-way

The transaction will automatically rollback. Fix the migration and restart.

### Need to add a new migration

Just create a new file with a later `MIGRATION_ID`. It will be picked up automatically.

### Want to see what migrations have been applied

```sql
SELECT * FROM schema_migrations ORDER BY id;
```

### Fresh database setup

When creating a fresh database:
1. SQLAlchemy creates base tables from models (`init_db()`)
2. Migration runner applies any additional migrations
3. Both paths lead to the same final schema

## Migration vs Model

- **Models** (`app/models.py`): Define the current, desired schema
- **Migrations**: Record the steps to get there from any previous state

For a fresh database:
- Models create the base schema
- Migrations apply any additional changes not captured in models

For an existing database:
- Models define the target
- Migrations bridge the gap from old schema to new
