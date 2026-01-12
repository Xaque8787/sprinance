# Database Migrations

This directory contains all database migration scripts for the Management System.

## Migration Files

Run migrations in the following order:

1. **migrate_database.py**
   - Initial database setup migration
   - Creates core tables and schema

2. **migrate_to_crud_system.py**
   - Migrates the system to use CRUD-based architecture
   - Major structural changes to support dynamic financial items

3. **add_crud_financial_items_migration.py**
   - Adds CRUD financial line items functionality
   - Creates `financial_line_item_templates` table
   - Creates `daily_financial_line_items` table
   - Adds `tips_on_paycheck` column to `daily_employee_entries`
   - Populates default financial templates

4. **remove_old_fields_migration.py**
   - Removes deprecated fields from the database
   - Cleans up old schema after CRUD migration

5. **add_tip_out_field.py**
   - Adds `tip_out` column to `daily_employee_entries` table
   - Allows tracking tip-outs that are subtracted from take-home tips

6. **update_tip_requirements_and_positions.py**
   - Adds new tip entry requirements: Adjustments, Tips on Paycheck, Tip Out
   - Updates all default positions with correct tip requirements
   - Adds new "Prep" position

7. **add_display_order_to_tip_requirements.py**
   - Adds `display_order` column to `tip_entry_requirements` table
   - Sets default display order values for existing requirements
   - Enables global ordering of tip requirements across all positions

8. **remove_display_order_from_position_tip_requirements.py**
   - Removes `display_order` column from `position_tip_requirements` junction table
   - Migrates to global tip requirement ordering system
   - Preserves all existing position-requirement associations

## Running Migrations

To run a specific migration:

```bash
python3 migrations/<migration_file_name>.py
```

To run all migrations in order:

```bash
python3 migrations/migrate_database.py
python3 migrations/migrate_to_crud_system.py
python3 migrations/add_crud_financial_items_migration.py
python3 migrations/remove_old_fields_migration.py
python3 migrations/add_tip_out_field.py
python3 migrations/update_tip_requirements_and_positions.py
python3 migrations/add_display_order_to_tip_requirements.py
python3 migrations/remove_display_order_from_position_tip_requirements.py
```

Or use the automated script:

```bash
python3 migrations/run_all_migrations.py
```

## Notes

- All migrations are idempotent and can be run multiple times safely
- Each migration checks if changes already exist before applying them
- Migrations use SQLite's `ALTER TABLE` for adding columns
- Default values are provided for all new columns to maintain data integrity
