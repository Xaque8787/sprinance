"""
Migration: Make Tip Fields Fully Dynamic

This migration removes hard-coded tip entry fields from the daily_employee_entries table
and ensures all data is stored in the tip_values JSON column.

Changes:
1. Migrates data from hard-coded columns (bank_card_sales, bank_card_tips, etc.) to tip_values JSON
2. Drops the hard-coded columns
3. Makes the system fully dynamic based on tip_entry_requirements

IMPORTANT: This migration should be run after ensuring all tip entry requirements
           have the correct field_name values.
"""

import sqlite3
import json
import os

def run_migration():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Starting migration: Make Tip Fields Fully Dynamic")

    cursor.execute("SELECT COUNT(*) FROM daily_employee_entries")
    total_entries = cursor.fetchone()[0]
    print(f"Found {total_entries} daily employee entries to migrate")

    cursor.execute("""
        SELECT id, bank_card_sales, bank_card_tips, cash_tips, total_sales,
               adjustments, tips_on_paycheck, tip_out, calculated_take_home, tip_values
        FROM daily_employee_entries
    """)

    entries = cursor.fetchall()
    migrated_count = 0

    for entry_id, bank_card_sales, bank_card_tips, cash_tips, total_sales, \
        adjustments, tips_on_paycheck, tip_out, calculated_take_home, tip_values_json in entries:

        tip_values = json.loads(tip_values_json) if tip_values_json else {}

        if bank_card_sales is not None and 'bank_card_sales' not in tip_values:
            tip_values['bank_card_sales'] = bank_card_sales
        if bank_card_tips is not None and 'bank_card_tips' not in tip_values:
            tip_values['bank_card_tips'] = bank_card_tips
        if cash_tips is not None and 'cash_tips' not in tip_values:
            tip_values['cash_tips'] = cash_tips
        if total_sales is not None and 'total_sales' not in tip_values:
            tip_values['total_sales'] = total_sales
        if adjustments is not None and 'adjustments' not in tip_values:
            tip_values['adjustments'] = adjustments
        if tips_on_paycheck is not None and 'tips_on_paycheck' not in tip_values:
            tip_values['tips_on_paycheck'] = tips_on_paycheck
        if tip_out is not None and 'tip_out' not in tip_values:
            tip_values['tip_out'] = tip_out
        if calculated_take_home is not None and 'calculated_take_home' not in tip_values:
            tip_values['calculated_take_home'] = calculated_take_home

        cursor.execute("""
            UPDATE daily_employee_entries
            SET tip_values = ?
            WHERE id = ?
        """, (json.dumps(tip_values), entry_id))

        migrated_count += 1

    print(f"Migrated {migrated_count} entries to tip_values JSON")

    print("Dropping hard-coded columns from daily_employee_entries...")

    cursor.execute("PRAGMA foreign_keys=off")

    cursor.execute("""
        CREATE TABLE daily_employee_entries_new (
            id INTEGER PRIMARY KEY,
            daily_balance_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            tip_values TEXT,
            FOREIGN KEY (daily_balance_id) REFERENCES daily_balance (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    """)

    cursor.execute("""
        INSERT INTO daily_employee_entries_new (id, daily_balance_id, employee_id, tip_values)
        SELECT id, daily_balance_id, employee_id, tip_values
        FROM daily_employee_entries
    """)

    cursor.execute("DROP TABLE daily_employee_entries")

    cursor.execute("ALTER TABLE daily_employee_entries_new RENAME TO daily_employee_entries")

    cursor.execute("PRAGMA foreign_keys=on")

    conn.commit()
    print("Migration completed successfully!")
    print("All tip fields are now fully dynamic and stored in tip_values JSON column")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_migration()
