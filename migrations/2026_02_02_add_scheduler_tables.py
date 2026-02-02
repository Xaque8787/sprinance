"""
# Create Scheduler Tables

## Overview
This migration creates the scheduler infrastructure tables needed for automated task
scheduling and execution tracking.

## Changes Made

### 1. New Tables

#### `scheduled_tasks`
Stores scheduled task configurations:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `name` (TEXT, NOT NULL): Display name for the task
- `task_type` (TEXT, NOT NULL): Type of task (tip_report, daily_balance_report, employee_tip_report, backup)
- `schedule_type` (TEXT, NOT NULL): Schedule type (cron or interval)
- `cron_expression` (TEXT): Cron expression for cron-based schedules
- `interval_value` (INTEGER): Interval value for interval-based schedules
- `interval_unit` (TEXT): Interval unit (minutes, hours, days, weeks)
- `start_date` (TEXT): Start date for the schedule
- `end_date` (TEXT): End date for the schedule
- `date_range_type` (TEXT): Date range type for reports (previous_day, previous_week, etc.)
- `email_list` (TEXT): JSON array of email addresses
- `bypass_opt_in` (BOOLEAN): Whether to bypass user opt-in preferences
- `is_active` (BOOLEAN): Whether the task is active
- `created_at` (TIMESTAMP): When the task was created
- `updated_at` (TIMESTAMP): When the task was last updated
- `last_run_at` (TIMESTAMP): When the task last ran
- `next_run_at` (TIMESTAMP): When the task will next run
- `employee_id` (INTEGER, FOREIGN KEY): Employee ID for employee-specific reports
- `starts_at` (TIMESTAMP): Task begins at this time (for interval schedules)

#### `task_executions`
Stores execution history for scheduled tasks:
- `id` (INTEGER, PRIMARY KEY): Unique identifier
- `task_id` (INTEGER, FOREIGN KEY): References scheduled_tasks.id
- `started_at` (TIMESTAMP): When the execution started
- `completed_at` (TIMESTAMP): When the execution completed
- `status` (TEXT, NOT NULL): Execution status (running, success, failed)
- `error_message` (TEXT): Error message if failed
- `result_data` (TEXT): JSON data about the execution result

### 2. Indexes

- `idx_task_executions_task_id_started`: Composite index on task_id and started_at
  for efficient execution history queries

### 3. Security & Data Integrity

- Task executions cascade delete when the parent scheduled_task is deleted
- Foreign key constraints ensure referential integrity
- Indexes optimize query performance for execution history

### 4. Important Notes

- Tasks can be paused/activated using the is_active flag
- Execution history is automatically cleaned up (keeps last 10 per task)
- Last run and next run times are automatically updated after each execution
- Employee ID is optional and only used for employee-specific report tasks
"""

MIGRATION_ID = "2026_02_02_add_scheduler_tables"


def upgrade(conn, column_exists, table_exists):
    """Create scheduler tables"""
    cursor = conn.cursor()

    if not table_exists('scheduled_tasks'):
        cursor.execute("""
            CREATE TABLE scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                schedule_type TEXT NOT NULL,
                cron_expression TEXT,
                interval_value INTEGER,
                interval_unit TEXT,
                start_date TEXT,
                end_date TEXT,
                date_range_type TEXT,
                email_list TEXT,
                bypass_opt_in INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run_at TIMESTAMP,
                next_run_at TIMESTAMP,
                employee_id INTEGER,
                starts_at TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """)
        print("  ✓ Created scheduled_tasks table")
    else:
        print("  ℹ️  scheduled_tasks table already exists, skipping")

    if not table_exists('task_executions'):
        cursor.execute("""
            CREATE TABLE task_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT NOT NULL,
                error_message TEXT,
                result_data TEXT,
                FOREIGN KEY (task_id) REFERENCES scheduled_tasks (id) ON DELETE CASCADE
            )
        """)
        print("  ✓ Created task_executions table")
    else:
        print("  ℹ️  task_executions table already exists, skipping")

    # Create index for task_executions cleanup
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_task_executions_task_id_started
        ON task_executions(task_id, started_at DESC)
    """)
    print("  ✓ Created index on task_executions")
