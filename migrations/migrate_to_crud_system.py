"""
Comprehensive migration script to transition to CRUD financial items system.

This migration:
1. Creates new tables for CRUD financial line items
2. Adds tips_on_paycheck column to daily_employee_entries
3. Migrates existing hardcoded financial data to the new CRUD structure
4. Removes old hardcoded columns from daily_balance table
5. Populates default financial line item templates
"""
import sqlite3
import os
from datetime import datetime

def migrate():
    db_path = "data/database.db"

    if not os.path.exists(db_path):
        print("Database does not exist. Will be created with new structure on first run.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting comprehensive migration to CRUD financial system...")

        # 1. Check and add tips_on_paycheck to daily_employee_entries
        cursor.execute("PRAGMA table_info(daily_employee_entries)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'tips_on_paycheck' not in columns:
            print("Adding tips_on_paycheck column to daily_employee_entries...")
            cursor.execute("""
                ALTER TABLE daily_employee_entries
                ADD COLUMN tips_on_paycheck REAL DEFAULT 0.0
            """)
        else:
            print("tips_on_paycheck column already exists")

        # 2. Create financial_line_item_templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_line_item_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                is_default INTEGER DEFAULT 0
            )
        """)
        print("Created financial_line_item_templates table")

        # 3. Create daily_financial_line_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_financial_line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_balance_id INTEGER NOT NULL,
                template_id INTEGER,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                value REAL DEFAULT 0.0,
                display_order INTEGER DEFAULT 0,
                is_employee_tip INTEGER DEFAULT 0,
                employee_id INTEGER,
                FOREIGN KEY (daily_balance_id) REFERENCES daily_balance(id),
                FOREIGN KEY (template_id) REFERENCES financial_line_item_templates(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """)
        print("Created daily_financial_line_items table")

        # 4. Populate default templates
        cursor.execute("SELECT COUNT(*) FROM financial_line_item_templates WHERE is_default = 1")
        default_count = cursor.fetchone()[0]

        if default_count == 0:
            print("Populating default financial line item templates...")

            revenue_items = [
                ("Cash Drawers Beginning", "revenue", 0),
                ("Food Sales", "revenue", 1),
                ("Non Alcohol Beverage Sales", "revenue", 2),
                ("Beer Sales", "revenue", 3),
                ("Wine Sales", "revenue", 4),
                ("Other Revenue", "revenue", 5),
                ("Catering Sales", "revenue", 6),
                ("Fundraising Contributions", "revenue", 7),
                ("Sales Tax Payable", "revenue", 8),
                ("Gift Certificate Sold", "revenue", 9),
            ]

            for name, category, order in revenue_items:
                cursor.execute("""
                    INSERT INTO financial_line_item_templates (name, category, display_order, is_default)
                    VALUES (?, ?, ?, 1)
                """, (name, category, order))

            expense_items = [
                ("Gift Certificate Redeemed", "expense", 0),
                ("Checking Account Cash Deposit", "expense", 1),
                ("Checking Account Bank Cards", "expense", 2),
                ("Cash Paid Out", "expense", 3),
                ("Cash Drawers End", "expense", 4),
            ]

            for name, category, order in expense_items:
                cursor.execute("""
                    INSERT INTO financial_line_item_templates (name, category, display_order, is_default)
                    VALUES (?, ?, ?, 1)
                """, (name, category, order))

            print(f"Added {len(revenue_items)} revenue and {len(expense_items)} expense default templates")
        else:
            print("Default templates already exist")

        # 5. Migrate existing daily_balance data to financial_line_items
        cursor.execute("PRAGMA table_info(daily_balance)")
        db_columns = [col[1] for col in cursor.fetchall()]

        old_columns_to_migrate = [
            ('cash_drawers_beginning', 'Cash Drawers Beginning', 'revenue'),
            ('food_sales', 'Food Sales', 'revenue'),
            ('non_alcohol_beverage_sales', 'Non Alcohol Beverage Sales', 'revenue'),
            ('beer_sales', 'Beer Sales', 'revenue'),
            ('wine_sales', 'Wine Sales', 'revenue'),
            ('other_revenue', 'Other Revenue', 'revenue'),
            ('catering_sales', 'Catering Sales', 'revenue'),
            ('fundraising_contributions', 'Fundraising Contributions', 'revenue'),
            ('sales_tax_payable', 'Sales Tax Payable', 'revenue'),
            ('gift_certificate_sold', 'Gift Certificate Sold', 'revenue'),
            ('gift_certificate_redeemed', 'Gift Certificate Redeemed', 'expense'),
            ('checking_account_cash_deposit', 'Checking Account Cash Deposit', 'expense'),
            ('checking_account_bank_cards', 'Checking Account Bank Cards', 'expense'),
            ('cash_paid_out', 'Cash Paid Out', 'expense'),
            ('cash_drawers_end', 'Cash Drawers End', 'expense'),
        ]

        # Check if any old columns exist
        old_cols_present = [col for col, _, _ in old_columns_to_migrate if col in db_columns]

        if old_cols_present:
            print(f"Found {len(old_cols_present)} old columns to migrate...")

            # Get all daily_balance records
            cursor.execute("SELECT id, * FROM daily_balance")
            balance_records = cursor.fetchall()

            # Get column indices
            cursor.execute("PRAGMA table_info(daily_balance)")
            col_info = cursor.fetchall()
            col_names = [col[1] for col in col_info]

            for record in balance_records:
                balance_id = record[0]

                # Check if this balance already has financial_line_items
                cursor.execute("SELECT COUNT(*) FROM daily_financial_line_items WHERE daily_balance_id = ?", (balance_id,))
                existing_items = cursor.fetchone()[0]

                if existing_items == 0:
                    # Migrate data from old columns
                    for col_name, display_name, category in old_columns_to_migrate:
                        if col_name in col_names:
                            col_idx = col_names.index(col_name)
                            value = record[col_idx] if record[col_idx] is not None else 0.0

                            # Get template_id for this item
                            cursor.execute(
                                "SELECT id, display_order FROM financial_line_item_templates WHERE name = ?",
                                (display_name,)
                            )
                            template_row = cursor.fetchone()

                            if template_row:
                                template_id, display_order = template_row

                                cursor.execute("""
                                    INSERT INTO daily_financial_line_items
                                    (daily_balance_id, template_id, name, category, value, display_order, is_employee_tip)
                                    VALUES (?, ?, ?, ?, ?, ?, 0)
                                """, (balance_id, template_id, display_name, category, value, display_order))

            print(f"Migrated data for {len(balance_records)} daily balance records")

            # 6. Remove old columns from daily_balance table
            print("Removing old columns from daily_balance table...")

            # Get current table schema
            cursor.execute("PRAGMA table_info(daily_balance)")
            all_columns = cursor.fetchall()

            # Columns to keep
            cols_to_keep = ['id', 'date', 'day_of_week', 'notes', 'finalized']
            new_columns = [col for col in all_columns if col[1] in cols_to_keep]

            # Get all data
            cursor.execute("SELECT * FROM daily_balance")
            all_data = cursor.fetchall()

            # Create new table
            col_defs = []
            for col in new_columns:
                col_name = col[1]
                col_type = col[2]
                col_def = f"{col_name} {col_type}"

                if col[3]:  # NOT NULL
                    col_def += " NOT NULL"
                if col[4] is not None:  # DEFAULT
                    col_def += f" DEFAULT {col[4]}"
                if col[5]:  # PRIMARY KEY
                    col_def += " PRIMARY KEY"

                col_defs.append(col_def)

            create_statement = f"CREATE TABLE daily_balance_new ({', '.join(col_defs)})"
            cursor.execute(create_statement)

            # Copy data
            if all_data:
                old_col_names = [col[1] for col in all_columns]
                new_col_names = [col[1] for col in new_columns]
                indices_to_keep = [old_col_names.index(name) for name in new_col_names]

                placeholders = ','.join(['?' for _ in new_col_names])
                insert_statement = f"INSERT INTO daily_balance_new ({','.join(new_col_names)}) VALUES ({placeholders})"

                new_rows = [[row[i] for i in indices_to_keep] for row in all_data]
                cursor.executemany(insert_statement, new_rows)

            # Drop old table and rename
            cursor.execute("DROP TABLE daily_balance")
            cursor.execute("ALTER TABLE daily_balance_new RENAME TO daily_balance")

            # Recreate index
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_daily_balance_date ON daily_balance(date)")

            print("Successfully removed old columns and restructured daily_balance table")
        else:
            print("Old columns already removed or not present")

        conn.commit()
        print("\nMigration completed successfully!")
        print("The system now uses CRUD financial line items.")

    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
