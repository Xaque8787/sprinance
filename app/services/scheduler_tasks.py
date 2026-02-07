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

def force_update_execution_status(execution_id, status, result_data=None, error_message=None):
    """
    Force update execution status using a fresh database connection.
    This is a last-resort function to ensure status is updated even if
    the main session has issues.
    """
    db = SessionLocal()
    try:
        print(f"  → [FORCE UPDATE] Creating fresh DB connection for execution {execution_id}")

        if status == 'success':
            db.execute(text("""
                UPDATE task_executions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'success',
                    result_data = :result_data
                WHERE id = :execution_id
            """), {"execution_id": execution_id, "result_data": result_data})
        else:
            db.execute(text("""
                UPDATE task_executions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'failed',
                    error_message = :error_message
                WHERE id = :execution_id
            """), {"execution_id": execution_id, "error_message": error_message})

        db.commit()
        print(f"  → [FORCE UPDATE] Status updated to '{status}' and committed")

        # Verify it stuck
        verify = db.execute(text("""
            SELECT status FROM task_executions WHERE id = :execution_id
        """), {"execution_id": execution_id}).scalar()
        print(f"  → [FORCE UPDATE] Verification: status is '{verify}'")

        return True
    except Exception as e:
        print(f"  ✗ [FORCE UPDATE] Failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def commit_with_retry(db, max_retries=5, base_delay=0.1):
    """
    Attempt to commit database changes with retry logic for SQLite locking issues.

    Args:
        db: Database session
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will increase exponentially)

    Returns:
        bool: True if commit succeeded, False otherwise
    """
    print(f"  → [COMMIT] Attempting to commit transaction (max {max_retries} attempts)...")

    for attempt in range(max_retries):
        try:
            db.commit()
            print(f"  ✓ [COMMIT] Successfully committed on attempt {attempt + 1}")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"  ⚠ [COMMIT] Database locked, retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay)
                db.rollback()
            else:
                print(f"  ✗ [COMMIT] Database commit failed after {max_retries} attempts: {e}")
                import traceback
                traceback.print_exc()
                db.rollback()
                return False
        except Exception as e:
            print(f"  ✗ [COMMIT] Unexpected error during commit: {e}")
            import traceback
            traceback.print_exc()
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

def run_tip_report_task(task_id, task_name, date_range_type, email_list_json, bypass_opt_in, attach_csv=False):
    """
    Generate and email a tip report.

    Args:
        task_id: Scheduled task ID
        task_name: Name of the task
        date_range_type: Type of date range (e.g., 'previous_week')
        email_list_json: JSON string of email addresses
        bypass_opt_in: Whether to bypass email opt-in preference (0 or 1)
        attach_csv: Whether to attach CSV file to email (default: False)
    """
    print(f"\n{'='*80}")
    print(f"▶️  TASK TRIGGERED: '{task_name}' (ID: {task_id}) at {datetime.now()}")
    print(f"{'='*80}\n")

    db = SessionLocal()
    execution_id = None
    task_succeeded = False
    final_result_data = None

    try:
        print(f"  → Starting tip report task '{task_name}' (ID: {task_id})")

        # Verify the task exists before creating execution
        task_exists = db.execute(text("""
            SELECT COUNT(*) FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id}).scalar()

        if not task_exists:
            raise Exception(f"Task ID {task_id} does not exist in scheduled_tasks table")

        start_date, end_date = calculate_date_range(date_range_type)
        print(f"  → Date range: {start_date} to {end_date}")

        db.execute(text("""
            INSERT INTO task_executions (task_id, started_at, status)
            VALUES (:task_id, CURRENT_TIMESTAMP, 'running')
        """), {"task_id": task_id})

        if not commit_with_retry(db):
            raise Exception("Failed to create task execution record")

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        if not execution_id or execution_id == 0:
            raise Exception(f"Failed to get valid execution_id (got: {execution_id}). This may indicate a foreign key constraint issue or missing task_id: {task_id}")

        print(f"  → Created execution record (ID: {execution_id})")

        filename = generate_tip_report_csv(db, start_date, end_date, current_user=None, source="scheduled_task")
        year = str(start_date.year)
        month = f"{start_date.month:02d}"
        filepath = os.path.join(DATABASE_DIR, "reports", "tip_report", year, month, filename)

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
                date_range=date_range,
                attach_csv=attach_csv
            )

            if not result["success"]:
                raise Exception(f"Email sending failed: {result.get('message', 'Unknown error')}")

        print(f"  → Report generated: {filename}")
        print(f"  → Emails sent: {len(email_list)}")

        final_result_data = json.dumps({
            "filename": filename,
            "date_range": f"{start_date} to {end_date}",
            "emails_sent": len(email_list)
        })

        print(f"  → [CRITICAL] Marking execution {execution_id} as SUCCESS...")

        time.sleep(0.05)

        db.execute(text("""
            UPDATE task_executions
            SET completed_at = CURRENT_TIMESTAMP,
                status = 'success',
                result_data = :result_data
            WHERE id = :execution_id
        """), {"execution_id": execution_id, "result_data": final_result_data})

        print(f"  → [CRITICAL] UPDATE statement executed, attempting commit...")

        commit_success = commit_with_retry(db)
        print(f"  → [CRITICAL] Commit result: {commit_success}")

        if not commit_success:
            raise Exception("Failed to commit task execution status to success")

        # Verify status immediately after commit
        verification = db.execute(text("""
            SELECT status, completed_at FROM task_executions WHERE id = :execution_id
        """), {"execution_id": execution_id}).fetchone()

        print(f"  → [CRITICAL] Verification check: status='{verification[0]}', completed_at='{verification[1]}'")

        if verification[0] != 'success':
            raise Exception(f"Status verification FAILED: expected 'success', got '{verification[0]}'")

        print(f"  ✓ [SUCCESS] Execution {execution_id} confirmed as 'success' in database")

        # Mark that task succeeded for finally block
        task_succeeded = True

        time.sleep(0.05)

        print(f"  → Updating scheduled task metadata...")

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
            print(f"  ⚠ Warning: Failed to update scheduled task metadata for '{task_name}'")
        else:
            print(f"  ✓ Task metadata updated")

        cleanup_old_executions(task_id)

        print(f"✓✓✓ Tip report task '{task_name}' COMPLETED SUCCESSFULLY ✓✓✓")

    except Exception as e:
        error_message = str(e)
        print(f"✗ Tip report task '{task_name}' failed: {error_message}")

        import traceback
        traceback.print_exc()

        if execution_id:
            try:
                time.sleep(0.05)
                db.execute(text("""
                    UPDATE task_executions
                    SET completed_at = CURRENT_TIMESTAMP,
                        status = 'failed',
                        error_message = :error_message
                    WHERE id = :execution_id
                """), {"execution_id": execution_id, "error_message": error_message})

                if commit_with_retry(db):
                    print(f"  ✓ Marked execution {execution_id} as failed")
                else:
                    print(f"  ✗ WARNING: Could not mark execution {execution_id} as failed!")
            except Exception as update_error:
                print(f"  ✗ ERROR updating execution status: {update_error}")
        else:
            print(f"  ✗ No execution_id available to mark as failed")

    finally:
        try:
            print(f"  → [FINALLY] Closing database connection...")
            db.close()
            print(f"  → [FINALLY] Database connection closed")

            # SAFETY CHECK: If task succeeded but might not have updated status, force update with new connection
            if task_succeeded and execution_id:
                print(f"  → [SAFETY] Task succeeded, verifying status with fresh connection...")
                verify_db = SessionLocal()
                try:
                    status_check = verify_db.execute(text("""
                        SELECT status FROM task_executions WHERE id = :execution_id
                    """), {"execution_id": execution_id}).scalar()

                    print(f"  → [SAFETY] Status is '{status_check}'")

                    if status_check != 'success':
                        print(f"  ⚠️  [SAFETY] Status is '{status_check}' but should be 'success'! Force updating...")
                        force_update_execution_status(execution_id, 'success', final_result_data)
                    else:
                        print(f"  ✓ [SAFETY] Status correctly set to 'success'")
                finally:
                    verify_db.close()

        except Exception as close_error:
            print(f"  ✗ [FINALLY] ERROR closing database: {close_error}")

def run_daily_balance_report_task(task_id, task_name, date_range_type, email_list_json, bypass_opt_in, attach_csv=False):
    """
    Generate and email a daily balance report.

    Args:
        task_id: Scheduled task ID
        task_name: Name of the task
        date_range_type: Type of date range (e.g., 'previous_month')
        email_list_json: JSON string of email addresses
        bypass_opt_in: Whether to bypass email opt-in preference (0 or 1)
        attach_csv: Whether to attach CSV file to email (default: False)
    """
    db = SessionLocal()
    execution_id = None

    try:
        print(f"▶️  Starting daily balance report task '{task_name}' (ID: {task_id})")

        # Verify the task exists before creating execution
        task_exists = db.execute(text("""
            SELECT COUNT(*) FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id}).scalar()

        if not task_exists:
            raise Exception(f"Task ID {task_id} does not exist in scheduled_tasks table")

        start_date, end_date = calculate_date_range(date_range_type)
        print(f"  → Date range: {start_date} to {end_date}")

        db.execute(text("""
            INSERT INTO task_executions (task_id, started_at, status)
            VALUES (:task_id, CURRENT_TIMESTAMP, 'running')
        """), {"task_id": task_id})

        if not commit_with_retry(db):
            raise Exception("Failed to create task execution record")

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        if not execution_id or execution_id == 0:
            raise Exception(f"Failed to get valid execution_id (got: {execution_id}). This may indicate a foreign key constraint issue or missing task_id: {task_id}")

        print(f"  → Created execution record (ID: {execution_id})")

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
                date_range=date_range,
                attach_csv=attach_csv
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

        # Clear session cache to ensure fresh data is read during verification
        db.expire_all()

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

        import traceback
        traceback.print_exc()

        if execution_id:
            try:
                time.sleep(0.05)
                db.execute(text("""
                    UPDATE task_executions
                    SET completed_at = CURRENT_TIMESTAMP,
                        status = 'failed',
                        error_message = :error_message
                    WHERE id = :execution_id
                """), {"execution_id": execution_id, "error_message": error_message})

                if commit_with_retry(db):
                    print(f"  ✓ Marked execution {execution_id} as failed")
                else:
                    print(f"  ✗ WARNING: Could not mark execution {execution_id} as failed!")
            except Exception as update_error:
                print(f"  ✗ ERROR updating execution status: {update_error}")
        else:
            print(f"  ✗ No execution_id available to mark as failed")

    finally:
        try:
            print(f"  → [FINALLY] Closing database connection...")
            db.close()
            print(f"  → [FINALLY] Database connection closed")
        except Exception as close_error:
            print(f"  ✗ [FINALLY] ERROR closing database: {close_error}")

def run_employee_tip_report_task(task_id, task_name, date_range_type, email_list_json, bypass_opt_in, employee_id, attach_csv=False):
    """
    Generate and email an employee tip report.

    Args:
        task_id: Scheduled task ID
        task_name: Name of the task
        date_range_type: Type of date range (e.g., 'previous_week')
        email_list_json: JSON string of email addresses
        bypass_opt_in: Whether to bypass email opt-in preference (0 or 1)
        employee_id: ID of the employee
        attach_csv: Whether to attach CSV file to email (default: False)
    """
    db = SessionLocal()
    execution_id = None

    try:
        print(f"▶️  Starting employee tip report task '{task_name}' (ID: {task_id})")

        # Verify the task exists before creating execution
        task_exists = db.execute(text("""
            SELECT COUNT(*) FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id}).scalar()

        if not task_exists:
            raise Exception(f"Task ID {task_id} does not exist in scheduled_tasks table")

        start_date, end_date = calculate_date_range(date_range_type)
        print(f"  → Date range: {start_date} to {end_date}")

        db.execute(text("""
            INSERT INTO task_executions (task_id, started_at, status)
            VALUES (:task_id, CURRENT_TIMESTAMP, 'running')
        """), {"task_id": task_id})

        if not commit_with_retry(db):
            raise Exception("Failed to create task execution record")

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        if not execution_id or execution_id == 0:
            raise Exception(f"Failed to get valid execution_id (got: {execution_id}). This may indicate a foreign key constraint issue or missing task_id: {task_id}")

        print(f"  → Created execution record (ID: {execution_id})")

        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise Exception(f"Employee with ID {employee_id} not found")

        filename = generate_employee_tip_report_csv(db, employee, start_date, end_date, current_user=None, source="scheduled_task")
        year = str(start_date.year)
        month = f"{start_date.month:02d}"
        filepath = os.path.join(DATABASE_DIR, "reports", "tip_report", year, month, filename)

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
                date_range=date_range,
                attach_csv=attach_csv
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

        # Clear session cache to ensure fresh data is read during verification
        db.expire_all()

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

        import traceback
        traceback.print_exc()

        if execution_id:
            try:
                time.sleep(0.05)
                db.execute(text("""
                    UPDATE task_executions
                    SET completed_at = CURRENT_TIMESTAMP,
                        status = 'failed',
                        error_message = :error_message
                    WHERE id = :execution_id
                """), {"execution_id": execution_id, "error_message": error_message})

                if commit_with_retry(db):
                    print(f"  ✓ Marked execution {execution_id} as failed")
                else:
                    print(f"  ✗ WARNING: Could not mark execution {execution_id} as failed!")
            except Exception as update_error:
                print(f"  ✗ ERROR updating execution status: {update_error}")
        else:
            print(f"  ✗ No execution_id available to mark as failed")

    finally:
        try:
            print(f"  → [FINALLY] Closing database connection...")
            db.close()
            print(f"  → [FINALLY] Database connection closed")
        except Exception as close_error:
            print(f"  ✗ [FINALLY] ERROR closing database: {close_error}")

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
        print(f"▶️  Starting backup task '{task_name}' (ID: {task_id})")

        # Verify the task exists before creating execution
        task_exists = db.execute(text("""
            SELECT COUNT(*) FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id}).scalar()

        if not task_exists:
            raise Exception(f"Task ID {task_id} does not exist in scheduled_tasks table")

        db.execute(text("""
            INSERT INTO task_executions (task_id, started_at, status)
            VALUES (:task_id, CURRENT_TIMESTAMP, 'running')
        """), {"task_id": task_id})

        if not commit_with_retry(db):
            raise Exception("Failed to create task execution record")

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        if not execution_id or execution_id == 0:
            raise Exception(f"Failed to get valid execution_id (got: {execution_id}). This may indicate a foreign key constraint issue or missing task_id: {task_id}")

        print(f"  → Created execution record (ID: {execution_id})")

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

        # Clear session cache to ensure fresh data is read during verification
        db.expire_all()

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

        import traceback
        traceback.print_exc()

        if execution_id:
            try:
                time.sleep(0.05)
                db.execute(text("""
                    UPDATE task_executions
                    SET completed_at = CURRENT_TIMESTAMP,
                        status = 'failed',
                        error_message = :error_message
                    WHERE id = :execution_id
                """), {"execution_id": execution_id, "error_message": error_message})

                if commit_with_retry(db):
                    print(f"  ✓ Marked execution {execution_id} as failed")
                else:
                    print(f"  ✗ WARNING: Could not mark execution {execution_id} as failed!")
            except Exception as update_error:
                print(f"  ✗ ERROR updating execution status: {update_error}")
        else:
            print(f"  ✗ No execution_id available to mark as failed")

    finally:
        try:
            print(f"  → [FINALLY] Closing database connection...")
            db.close()
            print(f"  → [FINALLY] Database connection closed")
        except Exception as close_error:
            print(f"  ✗ [FINALLY] ERROR closing database: {close_error}")
