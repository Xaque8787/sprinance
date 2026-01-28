"""
Migration: Add employee snapshot fields to allow safe deletion while preserving historical data

This migration:
1. Adds employee_name_snapshot and position_name_snapshot fields to daily_employee_entries
2. Adds employee_name_snapshot field to daily_financial_line_items
3. Makes employee_id nullable in daily_employee_entries
4. Populates existing records with snapshot data from current employee/position names
"""

from sqlalchemy import text
from app.database import engine

def upgrade():
    with engine.connect() as conn:
        print("Adding snapshot fields to daily_employee_entries...")
        conn.execute(text("""
            ALTER TABLE daily_employee_entries
            ADD COLUMN employee_name_snapshot TEXT;
        """))

        conn.execute(text("""
            ALTER TABLE daily_employee_entries
            ADD COLUMN position_name_snapshot TEXT;
        """))

        print("Adding snapshot field to daily_financial_line_items...")
        conn.execute(text("""
            ALTER TABLE daily_financial_line_items
            ADD COLUMN employee_name_snapshot TEXT;
        """))

        print("Populating snapshot data for daily_employee_entries...")
        conn.execute(text("""
            UPDATE daily_employee_entries
            SET employee_name_snapshot = (
                SELECT name FROM employees WHERE employees.id = daily_employee_entries.employee_id
            ),
            position_name_snapshot = (
                SELECT name FROM positions WHERE positions.id = daily_employee_entries.position_id
            )
            WHERE employee_id IS NOT NULL;
        """))

        print("Populating snapshot data for daily_financial_line_items...")
        conn.execute(text("""
            UPDATE daily_financial_line_items
            SET employee_name_snapshot = (
                SELECT name FROM employees WHERE employees.id = daily_financial_line_items.employee_id
            )
            WHERE employee_id IS NOT NULL;
        """))

        print("Creating new daily_employee_entries table with nullable employee_id...")
        conn.execute(text("""
            CREATE TABLE daily_employee_entries_new (
                id INTEGER PRIMARY KEY,
                daily_balance_id INTEGER NOT NULL,
                employee_id INTEGER,
                position_id INTEGER,
                tip_values TEXT,
                employee_name_snapshot TEXT,
                position_name_snapshot TEXT,
                FOREIGN KEY (daily_balance_id) REFERENCES daily_balance(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (position_id) REFERENCES positions(id)
            );
        """))

        print("Copying data to new table...")
        conn.execute(text("""
            INSERT INTO daily_employee_entries_new
            SELECT id, daily_balance_id, employee_id, position_id, tip_values,
                   employee_name_snapshot, position_name_snapshot
            FROM daily_employee_entries;
        """))

        print("Replacing old table with new table...")
        conn.execute(text("DROP TABLE daily_employee_entries;"))
        conn.execute(text("ALTER TABLE daily_employee_entries_new RENAME TO daily_employee_entries;"))

        conn.commit()
        print("Migration completed successfully!")

def downgrade():
    with engine.connect() as conn:
        print("Removing snapshot fields...")
        conn.execute(text("""
            ALTER TABLE daily_employee_entries
            DROP COLUMN employee_name_snapshot;
        """))

        conn.execute(text("""
            ALTER TABLE daily_employee_entries
            DROP COLUMN position_name_snapshot;
        """))

        conn.execute(text("""
            ALTER TABLE daily_financial_line_items
            DROP COLUMN employee_name_snapshot;
        """))

        conn.commit()
        print("Downgrade completed!")

if __name__ == "__main__":
    print("Running migration: add_employee_snapshots_for_deletion")
    upgrade()
