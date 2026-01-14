#!/bin/bash

# Script to add tip_values column to the database

echo "Adding tip_values column to daily_employee_entries table..."

# Method 1: Try using Python migration
if [ -f ".venv/bin/activate" ]; then
    echo "Using virtual environment..."
    source .venv/bin/activate
    python migrations/add_tip_values_json.py
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "Migration completed successfully!"
        exit 0
    fi
fi

# Method 2: Try using sqlite3 directly
if command -v sqlite3 &> /dev/null; then
    echo "Using sqlite3 directly..."
    sqlite3 data/database.db "ALTER TABLE daily_employee_entries ADD COLUMN tip_values TEXT DEFAULT '{}';" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Column added successfully!"
        exit 0
    else
        echo "Column may already exist or there was an error."
    fi
fi

echo "Done!"
