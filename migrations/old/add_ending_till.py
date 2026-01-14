import sqlite3
import os

def migrate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    if not os.path.exists(db_path):
        print("Database not found. Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT is_ending_till FROM financial_line_item_templates LIMIT 1")
        print("Column 'is_ending_till' already exists. Skipping column addition.")
    except sqlite3.OperationalError:
        print("Adding is_ending_till column to financial_line_item_templates table...")
        cursor.execute("ALTER TABLE financial_line_item_templates ADD COLUMN is_ending_till BOOLEAN DEFAULT 0")
        conn.commit()
        print("is_ending_till column added successfully.")

    cursor.execute("SELECT COUNT(*) FROM financial_line_item_templates WHERE name = 'Ending Till' AND category = 'revenue'")
    revenue_count = cursor.fetchone()[0]

    if revenue_count == 0:
        print("Adding 'Ending Till' to Revenue & Income category...")
        cursor.execute("""
            SELECT MAX(display_order) FROM financial_line_item_templates WHERE category = 'revenue'
        """)
        max_order_result = cursor.fetchone()[0]
        max_order = (max_order_result or 0) + 1

        cursor.execute("""
            INSERT INTO financial_line_item_templates
            (name, category, display_order, is_default, is_deduction, is_starting_till, is_ending_till)
            VALUES ('Ending Till', 'revenue', ?, 0, 0, 0, 1)
        """, (max_order,))
        conn.commit()
        print("'Ending Till' added to Revenue & Income successfully.")
    else:
        print("'Ending Till' already exists in Revenue & Income. Skipping.")

    cursor.execute("SELECT COUNT(*) FROM financial_line_item_templates WHERE name = 'Ending Till' AND category = 'expense'")
    expense_count = cursor.fetchone()[0]

    if expense_count == 0:
        print("Adding 'Ending Till' to Deposits & Expenses category...")
        cursor.execute("""
            SELECT MAX(display_order) FROM financial_line_item_templates WHERE category = 'expense'
        """)
        max_order_result = cursor.fetchone()[0]
        max_order = (max_order_result or 0) + 1

        cursor.execute("""
            INSERT INTO financial_line_item_templates
            (name, category, display_order, is_default, is_deduction, is_starting_till, is_ending_till)
            VALUES ('Ending Till', 'expense', ?, 0, 0, 0, 1)
        """, (max_order,))
        conn.commit()
        print("'Ending Till' added to Deposits & Expenses successfully.")
    else:
        print("'Ending Till' already exists in Deposits & Expenses. Skipping.")

    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
