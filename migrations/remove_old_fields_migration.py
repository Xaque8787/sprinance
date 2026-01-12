"""
Migration script to remove old fields from daily_balance table.
Removes: total_cash_sales, total_card_sales, total_tips_collected
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
        # Check if the columns exist
        cursor.execute("PRAGMA table_info(daily_balance)")
        columns = [col[1] for col in cursor.fetchall()]

        fields_to_remove = ['total_cash_sales', 'total_card_sales', 'total_tips_collected']
        existing_fields = [f for f in fields_to_remove if f in columns]

        if not existing_fields:
            print("Fields already removed. No migration needed.")
            conn.close()
            return

        print(f"Removing fields: {', '.join(existing_fields)}")

        # SQLite doesn't support DROP COLUMN directly for all versions
        # We need to recreate the table without those columns

        # 1. Get current data
        cursor.execute("SELECT * FROM daily_balance")
        rows = cursor.fetchall()

        # 2. Get column names
        cursor.execute("PRAGMA table_info(daily_balance)")
        all_columns_info = cursor.fetchall()

        # 3. Create new table without the removed fields
        new_columns = [col for col in all_columns_info if col[1] not in fields_to_remove]

        # Build CREATE TABLE statement
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

        # 4. Create the new table
        cursor.execute(create_statement)

        # 5. Copy data (excluding removed columns)
        old_col_names = [col[1] for col in all_columns_info]
        new_col_names = [col[1] for col in new_columns]

        # Find indices of columns to keep
        indices_to_keep = [old_col_names.index(name) for name in new_col_names]

        # Insert data
        if rows:
            placeholders = ','.join(['?' for _ in new_col_names])
            insert_statement = f"INSERT INTO daily_balance_new ({','.join(new_col_names)}) VALUES ({placeholders})"

            new_rows = [[row[i] for i in indices_to_keep] for row in rows]
            cursor.executemany(insert_statement, new_rows)

        # 6. Drop old table and rename new one
        cursor.execute("DROP TABLE daily_balance")
        cursor.execute("ALTER TABLE daily_balance_new RENAME TO daily_balance")

        # 7. Recreate indices
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_daily_balance_date ON daily_balance(date)")

        conn.commit()
        print("Migration completed successfully!")
        print(f"Removed {len(existing_fields)} field(s) from daily_balance table.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
