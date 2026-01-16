#!/bin/bash
set -e

echo "=========================================="
echo "Starting Internal Management System"
echo "=========================================="

# Display version information
if [ -f .dockerversion ]; then
    VERSION=$(cat .dockerversion)
    echo "Version: $VERSION"
fi

# Ensure data directory exists and has proper permissions
echo "Ensuring data directory exists..."
mkdir -p data

# Check if database exists and initialize if needed
if [ ! -f data/database.db ]; then
    echo "Database not found. Initializing with current schema..."
    python3 -c "from app.database import init_db; init_db(); print('Database initialized successfully!')"
else
    echo "Database exists."
fi

# Always run migrations to apply any new updates
echo ""
echo "Checking for database migrations..."
python3 run_migrations.py

echo "=========================================="
echo "Starting application..."
echo "=========================================="

# Execute the CMD passed to the container
exec "$@"
