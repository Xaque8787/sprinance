import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import create_engine, inspect, text

def verify_and_fix():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "data", "database.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

    print(f"Database path: {db_path}")
    print(f"Database URL: {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)

    # Check if table exists
    if 'financial_line_item_templates' not in inspector.get_table_names():
        print("ERROR: financial_line_item_templates table does not exist!")
        return

    # Check columns
    columns = [col['name'] for col in inspector.get_columns('financial_line_item_templates')]
    print(f"\nCurrent columns: {', '.join(columns)}")

    if 'is_starting_till' not in columns:
        print("\nColumn is_starting_till is MISSING. Adding it now...")
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE financial_line_item_templates
                ADD COLUMN is_starting_till BOOLEAN DEFAULT 0
            """))
            conn.commit()
            print("✓ Column added successfully!")
    else:
        print("\n✓ Column is_starting_till exists!")

    # Verify again
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('financial_line_item_templates')]
    print(f"\nFinal columns: {', '.join(columns)}")

if __name__ == "__main__":
    verify_and_fix()
