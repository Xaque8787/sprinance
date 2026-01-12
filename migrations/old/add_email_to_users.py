from sqlalchemy import create_engine, text, inspect
from app.database import SQLALCHEMY_DATABASE_URL

def upgrade():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)

    if 'users' not in inspector.get_table_names():
        print("Users table doesn't exist yet - skipping migration (will be created automatically)")
        return

    with engine.connect() as conn:
        try:
            columns = [col['name'] for col in inspector.get_columns('users')]
            if 'email' in columns:
                print("Email column already exists in users table")
                return

            conn.execute(text("""
                ALTER TABLE users ADD COLUMN email VARCHAR;
            """))
            conn.commit()
            print("Successfully added email column to users table")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            conn.rollback()
            raise

if __name__ == "__main__":
    upgrade()
