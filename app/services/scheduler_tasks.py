import os
import json
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import text
from app.database import SessionLocal, DATABASE_DIR
from app.models import User
from app.utils.csv_generator import generate_tip_report_csv, generate_consolidated_daily_balance_csv
from app.utils.email import send_report_emails
from app.scheduler import cleanup_old_executions

def calculate_date_range(date_range_type):
    """
    Calculate start and end dates based on the date range type.

    Args:
        date_range_type: String like 'previous_week', 'previous_2_weeks', 'previous_month', etc.

    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()

    if date_range_type == 'previous_week':
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
        end_date = today - timedelta(days=1)
        start_date = end_date - timedelta(days=6)
    elif date_range_type == 'previous_14_days':
        end_date = today - timedelta(days=1)
        start_date = end_date - timedelta(days=13)
    elif date_range_type == 'previous_30_days':
        end_date = today - timedelta(days=1)
        start_date = end_date - timedelta(days=29)
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
            INSERT INTO task_executions (task_id, status)
            VALUES (:task_id, 'running')
        """), {"task_id": task_id})
        db.commit()

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        filename = generate_tip_report_csv(db, start_date, end_date)
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

        db.execute(text("""
            UPDATE task_executions
            SET completed_at = CURRENT_TIMESTAMP,
                status = 'success',
                result_data = :result_data
            WHERE id = :execution_id
        """), {"execution_id": execution_id, "result_data": result_data})
        db.commit()

        db.execute(text("""
            UPDATE scheduled_tasks
            SET last_run_at = CURRENT_TIMESTAMP
            WHERE id = :task_id
        """), {"task_id": task_id})
        db.commit()

        cleanup_old_executions(task_id)

        print(f"✓ Tip report task '{task_name}' completed successfully")

    except Exception as e:
        error_message = str(e)
        print(f"✗ Tip report task '{task_name}' failed: {error_message}")

        if execution_id:
            db.execute(text("""
                UPDATE task_executions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'failed',
                    error_message = :error_message
                WHERE id = :execution_id
            """), {"execution_id": execution_id, "error_message": error_message})
            db.commit()

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
            INSERT INTO task_executions (task_id, status)
            VALUES (:task_id, 'running')
        """), {"task_id": task_id})
        db.commit()

        execution_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        filename = generate_consolidated_daily_balance_csv(db, start_date, end_date)

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

        db.execute(text("""
            UPDATE task_executions
            SET completed_at = CURRENT_TIMESTAMP,
                status = 'success',
                result_data = :result_data
            WHERE id = :execution_id
        """), {"execution_id": execution_id, "result_data": result_data})
        db.commit()

        db.execute(text("""
            UPDATE scheduled_tasks
            SET last_run_at = CURRENT_TIMESTAMP
            WHERE id = :task_id
        """), {"task_id": task_id})
        db.commit()

        cleanup_old_executions(task_id)

        print(f"✓ Daily balance report task '{task_name}' completed successfully")

    except Exception as e:
        error_message = str(e)
        print(f"✗ Daily balance report task '{task_name}' failed: {error_message}")

        if execution_id:
            db.execute(text("""
                UPDATE task_executions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'failed',
                    error_message = :error_message
                WHERE id = :execution_id
            """), {"execution_id": execution_id, "error_message": error_message})
            db.commit()

    finally:
        db.close()
