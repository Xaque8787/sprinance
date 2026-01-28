"""
Migration: Add Settings Table

This migration creates a settings table to store application configuration.
Initial setting: backup_retention_count (default: 7 backups)
"""

from sqlalchemy import text
from app.database import engine


def migrate():
    with engine.connect() as conn:
        try:
            print("Creating settings table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            print("Adding default backup retention setting...")
            conn.execute(text("""
                INSERT OR IGNORE INTO settings (key, value, description)
                VALUES ('backup_retention_count', '7', 'Number of database backups to keep')
            """))

            conn.commit()
            print("✓ Settings table created successfully")
            print("✓ Default backup retention set to 7 backups")

        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            raise


if __name__ == "__main__":
    migrate()
