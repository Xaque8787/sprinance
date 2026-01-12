#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

def upgrade():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR;
            """))
            conn.commit()
            print("Successfully added email column to users table")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            conn.rollback()
            raise

if __name__ == "__main__":
    upgrade()
