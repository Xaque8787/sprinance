"""
Migration script to add CRUD financial line items and tips_on_paycheck field.

Changes:
1. Add tips_on_paycheck column to daily_employee_entries
2. Create financial_line_item_templates table
3. Create daily_financial_line_items table
4. Populate default financial line item templates
"""
import sqlite3
import os

def migrate():
    db_path = "data/database.db"

    if not os.path.exists(db_path):
        print("Database does not exist. No migration needed.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting migration...")

        # 1. Add tips_on_paycheck to daily_employee_entries if it doesn't exist
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

        # 4. Check if default templates already exist
        cursor.execute("SELECT COUNT(*) FROM financial_line_item_templates WHERE is_default = 1")
        default_count = cursor.fetchone()[0]

        if default_count == 0:
            print("Populating default financial line item templates...")

            # Revenue & Income templates
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

            # Deposits & Expenses templates
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
            print("Default templates already exist, skipping...")

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
