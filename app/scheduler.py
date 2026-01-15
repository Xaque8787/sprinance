import os
import pytz
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy import text
from app.database import SCHEDULER_DIR, SessionLocal

# Get timezone from environment, default to America/Los_Angeles
TIMEZONE = os.getenv('TZ', 'America/Los_Angeles')
tz = pytz.timezone(TIMEZONE)

# Configure job stores
jobstores = {
    'default': SQLAlchemyJobStore(url=f'sqlite:///{SCHEDULER_DIR}/jobs.db')
}

executors = {
    'default': ThreadPoolExecutor(20)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 1,
    'misfire_grace_time': 300
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=tz
)

def get_next_run_times(schedule_type, cron_expression=None, interval_value=None, interval_unit=None, starts_at=None, count=5):
    """
    Calculate the next N run times for a schedule.

    Args:
        schedule_type: 'cron' or 'interval'
        cron_expression: Cron expression string (for cron schedules)
        interval_value: Interval value (for interval schedules)
        interval_unit: 'minutes', 'hours', 'days', 'weeks' (for interval schedules)
        starts_at: Starting datetime for interval schedules (optional, defaults to now)
        count: Number of next run times to calculate

    Returns:
        List of datetime objects representing next run times
    """
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger

    now = datetime.now(tz)
    next_runs = []

    try:
        if schedule_type == 'cron':
            parts = cron_expression.split()
            if len(parts) != 5:
                return []

            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                timezone=tz
            )

            current = now
            for _ in range(count):
                next_run = trigger.get_next_fire_time(None, current)
                if next_run:
                    next_runs.append(next_run)
                    current = next_run + timedelta(seconds=1)
                else:
                    break

        elif schedule_type == 'interval':
            kwargs = {interval_unit: interval_value}

            if starts_at:
                if isinstance(starts_at, str):
                    start_date = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                    if start_date.tzinfo is None:
                        start_date = tz.localize(start_date)
                    else:
                        start_date = start_date.astimezone(tz)
                else:
                    start_date = starts_at
            else:
                start_date = now

            trigger = IntervalTrigger(timezone=tz, start_date=start_date, **kwargs)

            current = now
            for _ in range(count):
                next_run = trigger.get_next_fire_time(None, current)
                if next_run:
                    next_runs.append(next_run)
                    current = next_run + timedelta(seconds=1)
                else:
                    break

    except Exception as e:
        print(f"Error calculating next run times: {e}")
        return []

    return next_runs

def cleanup_old_executions(task_id, keep_count=7):
    """
    Delete old task executions, keeping only the most recent N.

    Args:
        task_id: The scheduled task ID
        keep_count: Number of most recent executions to keep (default 7)
    """
    db = SessionLocal()
    try:
        # Get IDs of executions to delete (all except the most recent N)
        db.execute(text("""
            DELETE FROM task_executions
            WHERE task_id = :task_id
            AND id NOT IN (
                SELECT id FROM task_executions
                WHERE task_id = :task_id
                ORDER BY started_at DESC
                LIMIT :keep_count
            )
        """), {"task_id": task_id, "keep_count": keep_count})
        db.commit()
    except Exception as e:
        print(f"Error cleaning up old executions: {e}")
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    """Start the scheduler if not already running"""
    if not scheduler.running:
        scheduler.start()
        print(f"✓ Scheduler started with timezone: {TIMEZONE}")

def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        print("✓ Scheduler shut down gracefully")
