import sys
sys.path.insert(0, '/tmp/cc-agent/62753654/project')

from app.database import init_db, engine
from app.models import Base

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database initialized!")

print("\nRunning migration...")
import subprocess
result = subprocess.run(['python3', 'migrations/add_multi_position_and_inactive_status.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)
print("Migration complete!")
