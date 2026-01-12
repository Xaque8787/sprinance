import sqlite3
import os

def migrate_database():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    DATABASE_PATH = os.path.join(project_root, "data", "database.db")

    print(f"Looking for database at: {DATABASE_PATH}")

    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        print("No migration needed - database will be created with new schema on first run")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(daily_balance)")
    columns = [row[1] for row in cursor.fetchall()]

    new_columns = [
        ("cash_drawers_beginning", "FLOAT DEFAULT 0.0"),
        ("food_sales", "FLOAT DEFAULT 0.0"),
        ("non_alcohol_beverage_sales", "FLOAT DEFAULT 0.0"),
        ("beer_sales", "FLOAT DEFAULT 0.0"),
        ("wine_sales", "FLOAT DEFAULT 0.0"),
        ("other_revenue", "FLOAT DEFAULT 0.0"),
        ("catering_sales", "FLOAT DEFAULT 0.0"),
        ("fundraising_contributions", "FLOAT DEFAULT 0.0"),
        ("sales_tax_payable", "FLOAT DEFAULT 0.0"),
        ("gift_certificate_sold", "FLOAT DEFAULT 0.0"),
        ("gift_certificate_redeemed", "FLOAT DEFAULT 0.0"),
        ("checking_account_cash_deposit", "FLOAT DEFAULT 0.0"),
        ("checking_account_bank_cards", "FLOAT DEFAULT 0.0"),
        ("cash_paid_out", "FLOAT DEFAULT 0.0"),
        ("cash_drawers_end", "FLOAT DEFAULT 0.0")
    ]

    columns_added = []
    for column_name, column_type in new_columns:
        if column_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE daily_balance ADD COLUMN {column_name} {column_type}")
                columns_added.append(column_name)
                print(f"Added column: {column_name}")
            except Exception as e:
                print(f"Error adding column {column_name}: {e}")

    conn.commit()
    conn.close()

    if columns_added:
        print(f"\nMigration completed! Added {len(columns_added)} new columns.")
    else:
        print("\nNo migration needed - all columns already exist.")

def migrate():
    """Alias for consistency with other migration scripts."""
    return migrate_database()

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()
