from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Detect environment: Docker vs bare-metal/IDE
if os.path.exists('/app/data'):
    # Docker environment (working directory is /app)
    DATABASE_DIR = "/app/data"
    SCHEDULER_DIR = "/app/data/scheduler"
else:
    # Bare-metal/IDE environment (relative to project root)
    DATABASE_DIR = "data"
    SCHEDULER_DIR = "data/scheduler"

DATABASE_FILE = "database.db"
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_FILE)

# Create directories if they don't exist
for directory in [DATABASE_DIR, SCHEDULER_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

def database_exists():
    return os.path.exists(DATABASE_PATH)
