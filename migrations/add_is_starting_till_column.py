import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

def run_migration():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE financial_line_item_templates
            ADD COLUMN IF NOT EXISTS is_starting_till BOOLEAN DEFAULT FALSE
        """))
        conn.commit()
        print("Added is_starting_till column to financial_line_item_templates table")

if __name__ == "__main__":
    run_migration()
    print("Migration completed successfully!")
