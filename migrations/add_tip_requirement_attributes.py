"""
Migration: Add additional attributes to TipEntryRequirement

This migration adds new boolean fields to the tip_entry_requirements table
to support more flexible tip requirement configurations:
- is_total: Marks this as a calculated total field
- is_deduction: Marks this as a deduction from the total
- apply_to_revenue: Applies this value to Revenue & Income table
- revenue_is_deduction: Whether it's subtracted or added to revenue
- apply_to_expense: Applies this value to Deposits & Expenses table
- expense_is_deduction: Whether it's subtracted or added to expense
- no_null_value: Requires a positive value above 0
- no_input: No input field shown, acts as a placeholder/memo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal

def run_migration():
    db = SessionLocal()
    try:
        # Add new columns to tip_entry_requirements table
        columns_to_add = [
            ("is_total", "BOOLEAN DEFAULT FALSE"),
            ("is_deduction", "BOOLEAN DEFAULT FALSE"),
            ("apply_to_revenue", "BOOLEAN DEFAULT FALSE"),
            ("revenue_is_deduction", "BOOLEAN DEFAULT FALSE"),
            ("apply_to_expense", "BOOLEAN DEFAULT FALSE"),
            ("expense_is_deduction", "BOOLEAN DEFAULT FALSE"),
            ("no_null_value", "BOOLEAN DEFAULT FALSE"),
            ("no_input", "BOOLEAN DEFAULT FALSE")
        ]

        for column_name, column_type in columns_to_add:
            try:
                # Check if column already exists
                check_query = text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'tip_entry_requirements'
                    AND column_name = :column_name
                """)
                result = db.execute(check_query, {"column_name": column_name}).fetchone()

                if not result:
                    # Add the column if it doesn't exist
                    alter_query = text(f"""
                        ALTER TABLE tip_entry_requirements
                        ADD COLUMN {column_name} {column_type}
                    """)
                    db.execute(alter_query)
                    print(f"Added column: {column_name}")
                else:
                    print(f"Column {column_name} already exists, skipping")
            except Exception as e:
                print(f"Error adding column {column_name}: {e}")
                db.rollback()
                raise

        db.commit()
        print("Migration completed successfully")

    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
