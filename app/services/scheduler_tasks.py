import os
import json
import time
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import pytz
from app.database import SessionLocal, DATABASE_DIR
from app.models import User
from app.utils.csv_generator import generate_tip_report_csv, generate_consolidated_daily_balance_csv, generate_employee_tip_report_csv
from app.utils.email import send_report_emails
from app.scheduler import cleanup_old_executions
from app.utils.backup import create_backup
from app.models import Employee

def commit_with_retry(db, max_retries=3, base_delay=0.1):
    """
    Attempt to commit database changes with retry logic for SQLite locking issues.

    Args:
        db: Database session
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will increase exponentially)

    Returns:
        bool: True if commit succeeded, False otherwise
    """
    for attempt in range(max_retries):
        try:
            db.commit()
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⚠ Database locked, retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay)
                db.rollback()
            else:
                print(f"✗ Database commit failed after {max_retries} attempts: {e}")
                db.rollback()
                return False
        except Exception as e:
            print(f"✗ Unexpected error during commit: {e}")
            db.rollback()
            return False
    return False

def verify_execution_status(db, execution_id, expected_status):
    """
    Verify that a task execution has the expected status in the database.

    Args:
        db: Database session
        execution_id: The execution ID to check
        expected_status: The expected status ('success', 'failed', 'running')

    Returns:
        bool: True if status matches, False otherwise
    """
    try:
        result = db.execute(text("""
            SELECT status FROM task_executions WHERE id = :execution_id
        """), {"execution_id": execution_id}).fetchone()

        if result and result[0] == expected_status:
            return True
        else:
            print(f"⚠ Status mismatch: expected '{expected_status}', got '{result[0] if result else 'None'}'")
            return False
    except Exception as e:
        print(f"✗ Error verifying execution status: {e}")
        return False

def calculate_date_range(date_range_type):
    """
    Calculate start and end dates based on the date range type.
    Uses the configured timezone (TZ environment variable) to determine "today".

    For "previous_X_days" ranges, the end date is today (inclusive), and the start
    date is X-1 days before today, giving exactly X days of data including today.

    Example: "previous_14_days" on Jan 18 returns Jan 5 to Jan 18 (14 days).

    Args:
        date_range_type: String like 'previous_day', 'previous_week', 'previous_2_weeks', 'previous_month', etc.

    Returns:
        Tuple of (start_date, end_date)
    """
    TIMEZONE = os.getenv('TZ', 'America/Los_Angeles')
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    today = now.date()

    if date_range_type == 'previous_day':
        end_date = today - timedelta(days=1)
        start_date = end_date
    elif date_range_type == 'previous_week':
        end_date = today - timedelta(days=today.weekday() + 1)
        start_date = end_date - timedelta(days=6)
    elif date_range_type == 'previous_2_weeks':
        end_date = today - timedelta(days=today.weekday() + 1)
        start_date = end_date - timedelta(days=13)
    elif date_range_type == 'previous_month':
        first_of_this_month = today.replace(day=1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif date_range_type == 'previous_7_days':
        end_date = today
        start_date = today - timedelta(days=6)
    elif date_range_type == 'previous_14_days':
        end_date = today
        start_date = today - timedelta(days=13)
    elif date_range_type == 'previous_30_days':
        end_date = today
        start_date = today - timedelta(days=29)
    else:
        raise ValueError(f"Unknown date range type: {date_range_type}")

    return start_date, end_date

def run_tip_report_task(task_id, task_name, date_range_type, email_list_json, bypass_opt_in):
    """
    Generate and email a tip report.

    Args:
        task_id: Scheduled task ID
        task_name: Name of the task
        date_range_type: Type of date range (e.g., 'previous_week')
        email_list_json: JSON string of email addresses
        bypass_opt_in: Whether to bypass email opt-in preference (0 or 1)
    """
    db = SessionLocal()
    execution_id = None

    try:
        start_date, end_date = calculate_date_range(date_range_type)

        db.execute(text("""
            INSERT INTO task_executions (task_id, started_at, status)
            VALUES (:task_id, CURRENT_TIMESTAMP, 'running')
        """), {"task_id": task_id})

        if not commit_with_retry(db):
            raise Exception("Failed to create task execution record")

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        filename = generate_tip_report_csv(db, start_date, end_date, current_user=None, source="scheduled_task")
        filepath = os.path.join(DATABASE_DIR, "reports", "tip_report", filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Report file not found: {filepath}")

        email_list = json.loads(email_list_json) if email_list_json else []

        if not bypass_opt_in:
            opt_in_users = db.query(User).filter(
                User.opt_in_tip_reports == True,
                User.email.isnot(None),
                User.email != ""
            ).all()
            for user in opt_in_users:
                if user.email not in email_list:
                    email_list.append(user.email)

        if email_list:
            date_range = f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
            subject = f"[Scheduled] Tip Report - {date_range}"

            result = send_report_emails(
                to_emails=email_list,
                report_type="tips",
                report_filepath=filepath,
                subject=subject,
                date_range=date_range
            )

            if not result["success"]:
                raise Exception(f"Email sending failed: {result.get('message', 'Unknown error')}")

        result_data = json.dumps({
            "filename": filename,
            "date_range": f"{start_date} to {end_date}",
            "emails_sent": len(email_list)
        })

        time.sleep(0.05)

        db.execute(text("""
            UPDATE task_executions
            SET completed_at = CURRENT_TIMESTAMP,
                status = 'success',
                result_data = :result_data
            WHERE id = :execution_id
        """), {"execution_id": execution_id, "result_data": result_data})

        if not commit_with_retry(db):
            raise Exception("Failed to update task execution status to success")

        if not verify_execution_status(db, execution_id, 'success'):
            raise Exception("Task execution status verification failed")

        time.sleep(0.05)

        task_info = db.execute(text("""
            SELECT schedule_type, cron_expression, interval_value, interval_unit, starts_at
            FROM scheduled_tasks
            WHERE id = :task_id
        """), {"task_id": task_id}).fetchone()

        if task_info:
            from app.scheduler import get_next_run_times
            next_runs = get_next_run_times(
                schedule_type=task_info[0],
                cron_expression=task_info[1],
                interval_value=task_info[2],
                interval_unit=task_info[3],
                starts_at=task_info[4],
                count=1
            )
            next_run_at = next_runs[0].isoformat() if next_runs else None
        else:
            next_run_at = None

        db.execute(text("""
            UPDATE scheduled_tasks
            SET last_run_at = CURRENT_TIMESTAMP,
                next_run_at = :next_run_at
            WHERE id = :task_id
        """), {"task_id": task_id, "next_run_at": next_run_at})

        if not commit_with_retry(db):
            print(f"⚠ Warning: Failed to update scheduled task metadata for '{task_name}'")

        cleanup_old_executions(task_id)

        print(f"✓ Tip report task '{task_name}' completed successfully")

    except Exception as e:
        error_message = str(e)
        print(f"✗ Tip report task '{task_name}' failed: {error_message}")

        if execution_id:
            time.sleep(0.05)
            db.execute(text("""
                UPDATE task_executions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'failed',
                    error_message = :error_message
                WHERE id = :execution_id
            """), {"execution_id": execution_id, "error_message": error_message})
            commit_with_retry(db)

    finally:
        db.close()

def run_daily_balance_report_task(task_id, task_name, date_range_type, email_list_json, bypass_opt_in):
    """
    Generate and email a daily balance report.

    Args:
        task_id: Scheduled task ID
        task_name: Name of the task
        date_range_type: Type of date range (e.g., 'previous_month')
        email_list_json: JSON string of email addresses
        bypass_opt_in: Whether to bypass email opt-in preference (0 or 1)
    """
    db = SessionLocal()
    execution_id = None

    try:
        start_date, end_date = calculate_date_range(date_range_type)

        db.execute(text("""
            INSERT INTO task_executions (task_id, started_at, status)
            VALUES (:task_id, CURRENT_TIMESTAMP, 'running')
        """), {"task_id": task_id})

        if not commit_with_retry(db):
            raise Exception("Failed to create task execution record")

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        filename = generate_consolidated_daily_balance_csv(db, start_date, end_date, current_user=None, source="scheduled_task")

        year = str(start_date.year)
        month = f"{start_date.month:02d}"
        filepath = os.path.join(DATABASE_DIR, "reports", "daily_report", year, month, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Report file not found: {filepath}")

        email_list = json.loads(email_list_json) if email_list_json else []

        if not bypass_opt_in:
            opt_in_users = db.query(User).filter(
                User.opt_in_daily_reports == True,
                User.email.isnot(None),
                User.email != ""
            ).all()
            for user in opt_in_users:
                if user.email not in email_list:
                    email_list.append(user.email)

        if email_list:
            date_range = f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
            subject = f"[Scheduled] Daily Balance Report - {date_range}"

            result = send_report_emails(
                to_emails=email_list,
                report_type="daily",
                report_filepath=filepath,
                subject=subject,
                date_range=date_range
            )

            if not result["success"]:
                raise Exception(f"Email sending failed: {result.get('message', 'Unknown error')}")

        result_data = json.dumps({
            "filename": filename,
            "date_range": f"{start_date} to {end_date}",
            "emails_sent": len(email_list)
        })

        time.sleep(0.05)

        db.execute(text("""
            UPDATE task_executions
            SET completed_at = CURRENT_TIMESTAMP,
                status = 'success',
                result_data = :result_data
            WHERE id = :execution_id
        """), {"execution_id": execution_id, "result_data": result_data})

        if not commit_with_retry(db):
            raise Exception("Failed to update task execution status to success")

        if not verify_execution_status(db, execution_id, 'success'):
            raise Exception("Task execution status verification failed")

        time.sleep(0.05)

        task_info = db.execute(text("""
            SELECT schedule_type, cron_expression, interval_value, interval_unit, starts_at
            FROM scheduled_tasks
            WHERE id = :task_id
        """), {"task_id": task_id}).fetchone()

        if task_info:
            from app.scheduler import get_next_run_times
            next_runs = get_next_run_times(
                schedule_type=task_info[0],
                cron_expression=task_info[1],
                interval_value=task_info[2],
                interval_unit=task_info[3],
                starts_at=task_info[4],
                count=1
            )
            next_run_at = next_runs[0].isoformat() if next_runs else None
        else:
            next_run_at = None

        db.execute(text("""
            UPDATE scheduled_tasks
            SET last_run_at = CURRENT_TIMESTAMP,
                next_run_at = :next_run_at
            WHERE id = :task_id
        """), {"task_id": task_id, "next_run_at": next_run_at})

        if not commit_with_retry(db):
            print(f"⚠ Warning: Failed to update scheduled task metadata for '{task_name}'")

        cleanup_old_executions(task_id)

        print(f"✓ Daily balance report task '{task_name}' completed successfully")

    except Exception as e:
        error_message = str(e)
        print(f"✗ Daily balance report task '{task_name}' failed: {error_message}")

        if execution_id:
            time.sleep(0.05)
            db.execute(text("""
                UPDATE task_executions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'failed',
                    error_message = :error_message
                WHERE id = :execution_id
            """), {"execution_id": execution_id, "error_message": error_message})
            commit_with_retry(db)

    finally:
        db.close()

def run_employee_tip_report_task(task_id, task_name, date_range_type, email_list_json, bypass_opt_in, employee_id):
    """
    Generate and email an employee tip report.

    Args:
        task_id: Scheduled task ID
        task_name: Name of the task
        date_range_type: Type of date range (e.g., 'previous_week')
        email_list_json: JSON string of email addresses
        bypass_opt_in: Whether to bypass email opt-in preference (0 or 1)
        employee_id: ID of the employee
    """
    db = SessionLocal()
    execution_id = None

    try:
        start_date, end_date = calculate_date_range(date_range_type)

        db.execute(text("""
            INSERT INTO task_executions (task_id, started_at, status)
            VALUES (:task_id, CURRENT_TIMESTAMP, 'running')
        """), {"task_id": task_id})

        if not commit_with_retry(db):
            raise Exception("Failed to create task execution record")

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise Exception(f"Employee with ID {employee_id} not found")

        filename = generate_employee_tip_report_csv(db, employee, start_date, end_date, current_user=None, source="scheduled_task")
        filepath = os.path.join(DATABASE_DIR, "reports", "tip_report", filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Report file not found: {filepath}")

        email_list = json.loads(email_list_json) if email_list_json else []

        if not bypass_opt_in:
            opt_in_users = db.query(User).filter(
                User.opt_in_tip_reports == True,
                User.email.isnot(None),
                User.email != ""
            ).all()
            for user in opt_in_users:
                if user.email not in email_list:
                    email_list.append(user.email)

        if email_list:
            date_range = f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
            subject = f"[Scheduled] Employee Tip Report - {employee.name} - {date_range}"

            result = send_report_emails(
                to_emails=email_list,
                report_type="tips",
                report_filepath=filepath,
                subject=subject,
                date_range=date_range
            )

            if not result["success"]:
                raise Exception(f"Email sending failed: {result.get('message', 'Unknown error')}")

        result_data = json.dumps({
            "filename": filename,
            "employee_name": employee.name,
            "date_range": f"{start_date} to {end_date}",
            "emails_sent": len(email_list)
        })

        time.sleep(0.05)

        db.execute(text("""
            UPDATE task_executions
            SET completed_at = CURRENT_TIMESTAMP,
                status = 'success',
                result_data = :result_data
            WHERE id = :execution_id
        """), {"execution_id": execution_id, "result_data": result_data})

        if not commit_with_retry(db):
            raise Exception("Failed to update task execution status to success")

        if not verify_execution_status(db, execution_id, 'success'):
            raise Exception("Task execution status verification failed")

        time.sleep(0.05)

        task_info = db.execute(text("""
            SELECT schedule_type, cron_expression, interval_value, interval_unit, starts_at
            FROM scheduled_tasks
            WHERE id = :task_id
        """), {"task_id": task_id}).fetchone()

        if task_info:
            from app.scheduler import get_next_run_times
            next_runs = get_next_run_times(
                schedule_type=task_info[0],
                cron_expression=task_info[1],
                interval_value=task_info[2],
                interval_unit=task_info[3],
                starts_at=task_info[4],
                count=1
            )
            next_run_at = next_runs[0].isoformat() if next_runs else None
        else:
            next_run_at = None

        db.execute(text("""
            UPDATE scheduled_tasks
            SET last_run_at = CURRENT_TIMESTAMP,
                next_run_at = :next_run_at
            WHERE id = :task_id
        """), {"task_id": task_id, "next_run_at": next_run_at})

        if not commit_with_retry(db):
            print(f"⚠ Warning: Failed to update scheduled task metadata for '{task_name}'")

        cleanup_old_executions(task_id)

        print(f"✓ Employee tip report task '{task_name}' completed successfully")

    except Exception as e:
        error_message = str(e)
        print(f"✗ Employee tip report task '{task_name}' failed: {error_message}")

        if execution_id:
            time.sleep(0.05)
            db.execute(text("""
                UPDATE task_executions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'failed',
                    error_message = :error_message
                WHERE id = :execution_id
            """), {"execution_id": execution_id, "error_message": error_message})
            commit_with_retry(db)

    finally:
        db.close()

def run_backup_task(task_id, task_name):
    """
    Create a database backup.

    Args:
        task_id: Scheduled task ID
        task_name: Name of the task
    """
    db = SessionLocal()
    execution_id = None

    try:
        db.execute(text("""
            INSERT INTO task_executions (task_id, started_at, status)
            VALUES (:task_id, CURRENT_TIMESTAMP, 'running')
        """), {"task_id": task_id})

        if not commit_with_retry(db):
            raise Exception("Failed to create task execution record")

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        filename = create_backup()

        result_data = json.dumps({
            "filename": filename,
            "backup_created": True
        })

        time.sleep(0.05)

        db.execute(text("""
            UPDATE task_executions
            SET completed_at = CURRENT_TIMESTAMP,
                status = 'success',
                result_data = :result_data
            WHERE id = :execution_id
        """), {"execution_id": execution_id, "result_data": result_data})

        if not commit_with_retry(db):
            raise Exception("Failed to update task execution status to success")

        if not verify_execution_status(db, execution_id, 'success'):
            raise Exception("Task execution status verification failed")

        time.sleep(0.05)

        task_info = db.execute(text("""
            SELECT schedule_type, cron_expression, interval_value, interval_unit, starts_at
            FROM scheduled_tasks
            WHERE id = :task_id
        """), {"task_id": task_id}).fetchone()

        if task_info:
            from app.scheduler import get_next_run_times
            next_runs = get_next_run_times(
                schedule_type=task_info[0],
                cron_expression=task_info[1],
                interval_value=task_info[2],
                interval_unit=task_info[3],
                starts_at=task_info[4],
                count=1
            )
            next_run_at = next_runs[0].isoformat() if next_runs else None
        else:
            next_run_at = None

        db.execute(text("""
            UPDATE scheduled_tasks
            SET last_run_at = CURRENT_TIMESTAMP,
                next_run_at = :next_run_at
            WHERE id = :task_id
        """), {"task_id": task_id, "next_run_at": next_run_at})

        if not commit_with_retry(db):
            print(f"⚠ Warning: Failed to update scheduled task metadata for '{task_name}'")

        cleanup_old_executions(task_id)

        print(f"✓ Backup task '{task_name}' completed successfully")

    except Exception as e:
        error_message = str(e)
        print(f"✗ Backup task '{task_name}' failed: {error_message}")

        if execution_id:
            time.sleep(0.05)
            db.execute(text("""
                UPDATE task_executions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'failed',
                    error_message = :error_message
                WHERE id = :execution_id
            """), {"execution_id": execution_id, "error_message": error_message})
            commit_with_retry(db)

    finally:
        db.close()
