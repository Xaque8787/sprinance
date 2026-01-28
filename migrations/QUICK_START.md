# Migration Quick Start

## Create a New Migration

### 1. Create file in `/migrations`

```bash
touch migrations/2026_01_28_your_description.py
```

### 2. Use this template

```python
"""
Brief description of what this migration does.

More detailed explanation if needed, including:
- What tables are affected
- What data is migrated
- Any important considerations
"""

MIGRATION_ID = "2026_01_28_your_description"


def upgrade(conn, column_exists, table_exists):
    """
    Apply the migration.

    Args:
        conn: SQLite database connection
        column_exists: Helper - column_exists(table, column) -> bool
        table_exists: Helper - table_exists(table) -> bool
    """
    cursor = conn.cursor()

    # Your migration logic here
    # Always use defensive checks!

    if not column_exists('my_table', 'my_column'):
        cursor.execute("""
            ALTER TABLE my_table
            ADD COLUMN my_column TEXT DEFAULT 'default'
        """)
        print("  ✓ Added my_column to my_table")
    else:
        print("  ℹ️  my_column already exists, skipping")
```

### 3. Test locally

```bash
python run_migrations.py
```

### 4. Deploy

Commit and deploy. Migrations run automatically on container startup.

## Common Patterns

### Add a column

```python
if not column_exists('users', 'email'):
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

### Create a table

```python
if not table_exists('audit_log'):
    cursor.execute("""
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY,
            action TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

### Migrate data

```python
if column_exists('employees', 'old_field'):
    cursor.execute("""
        UPDATE employees
        SET new_field = old_field
        WHERE new_field IS NULL
    """)
```

### Recreate table (for column changes)

```python
cursor.execute("SELECT sql FROM sqlite_master WHERE name='my_table'")
table_sql = cursor.fetchone()[0]

if 'old_constraint' in table_sql:
    # Create new table
    cursor.execute("""
        CREATE TABLE my_table_new (
            id INTEGER PRIMARY KEY,
            name TEXT  -- modified
        )
    """)

    # Copy data
    cursor.execute("INSERT INTO my_table_new SELECT * FROM my_table")

    # Replace
    cursor.execute("DROP TABLE my_table")
    cursor.execute("ALTER TABLE my_table_new RENAME TO my_table")
```

## Naming Conventions

### Migration ID Format

`YYYY_MM_DD_brief_description`

**Examples:**
- `2026_01_28_add_user_email`
- `2026_02_15_create_audit_log`
- `2026_03_01_migrate_tip_data`

### File Name

Same as Migration ID: `2026_01_28_add_user_email.py`

## Checklist

Before deploying a migration:

- [ ] MIGRATION_ID is unique and follows format
- [ ] upgrade() function defined correctly
- [ ] Defensive checks in place (column_exists, table_exists)
- [ ] Tested locally with existing database
- [ ] Tested with fresh database
- [ ] Docstring explains what and why
- [ ] Print statements for feedback

## Testing

```bash
# Run migrations
python run_migrations.py

# Check status (requires sqlite3)
sqlite3 data/database.db "SELECT * FROM schema_migrations ORDER BY id;"

# Test idempotency (should skip already-applied migrations)
python run_migrations.py
```

## Troubleshooting

**Migration fails:**
- Check syntax errors
- Verify table/column names
- Test SQL in SQLite directly
- Check defensive conditions

**Migration applied but change missing:**
- Check if defensive condition prevented application
- Check migration logs for skip messages
- Verify database file path

**Need to re-run migration:**
```sql
DELETE FROM schema_migrations WHERE id = 'migration_id';
```
Then run `python run_migrations.py` again.

## More Information

- **Full guide**: `/migrations/README.md`
- **System architecture**: `/MIGRATION_SYSTEM.md`
- **Examples**: `/migrations/example_*.py.example`
