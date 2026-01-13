import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from app.database import SQLALCHEMY_DATABASE_URL, Base
from app.models import FinancialLineItemTemplate

def run_migration():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)

    if 'financial_line_item_templates' not in inspector.get_table_names():
        print("Tables don't exist yet. Creating all tables from models...")
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully including is_starting_till column")
    else:
        columns = [col['name'] for col in inspector.get_columns('financial_line_item_templates')]
        if 'is_starting_till' not in columns:
            with engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE financial_line_item_templates
                    ADD COLUMN is_starting_till BOOLEAN DEFAULT 0
                """))
                conn.commit()
                print("Added is_starting_till column to financial_line_item_templates table")
        else:
            print("is_starting_till column already exists, skipping...")

if __name__ == "__main__":
    run_migration()
    print("Migration completed successfully!")
