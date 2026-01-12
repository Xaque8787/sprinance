#!/usr/bin/env python3
"""
Wrapper script to run database migrations.
This is called by docker-entrypoint.sh during container startup.
"""

import sys
import os

# Add migrations directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'migrations'))

# Import and run the migrations
from migrations.run_all_migrations import run_all_migrations

if __name__ == "__main__":
    run_all_migrations()
