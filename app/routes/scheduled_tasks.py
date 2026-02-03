from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Optional
import json
from app.database import get_db, SessionLocal
from app.models import User, Employee
from app.auth.jwt_handler import get_current_user
from app.scheduler import scheduler, get_next_run_times
from app.services.scheduler_tasks import run_tip_report_task, run_daily_balance_report_task, run_employee_tip_report_task, run_backup_task

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def sync_next_run_times(db: Session):
    """
    Sync the next_run_at field in the database with APScheduler's actual next run time.
    This ensures the UI always displays the correct next run time.
    """
    tasks = db.execute(text("""
        SELECT id FROM scheduled_tasks WHERE is_active = 1
    """)).fetchall()

    for task_row in tasks:
        task_id = task_row[0]
        job_id = f"task_{task_id}"
        job = scheduler.get_job(job_id)

        if job and job.next_run_time:
            apscheduler_next_run = job.next_run_time.isoformat()

            db_next_run = db.execute(text("""
                SELECT next_run_at FROM scheduled_tasks WHERE id = :task_id
            """), {"task_id": task_id}).scalar()

            if db_next_run != apscheduler_next_run:
                db.execute(text("""
                    UPDATE scheduled_tasks
                    SET next_run_at = :next_run_at
                    WHERE id = :task_id
                """), {"next_run_at": apscheduler_next_run, "task_id": task_id})

    db.commit()

@router.get("/scheduled-tasks")
async def scheduled_tasks_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=303)

    import pytz
    import os
    TIMEZONE = os.getenv('TZ', 'America/Los_Angeles')
    tz = pytz.timezone(TIMEZONE)

    sync_next_run_times(db)

    tasks = db.execute(text("""
        SELECT * FROM scheduled_tasks
        ORDER BY created_at DESC
    """)).fetchall()

    tasks_with_executions = []
    for task in tasks:
        recent_executions = db.execute(text("""
            SELECT * FROM task_executions
            WHERE task_id = :task_id
            ORDER BY started_at DESC
            LIMIT 5
        """), {"task_id": task[0]}).fetchall()

        task_list = list(task)

        if task_list[15]:
            dt = datetime.fromisoformat(task_list[15].replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            task_list[15] = dt.astimezone(tz).strftime('%Y-%m-%d %I:%M:%S %p')

        if task_list[16]:
            dt = datetime.fromisoformat(task_list[16].replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            task_list[16] = dt.astimezone(tz).strftime('%Y-%m-%d %I:%M:%S %p')

        executions_list = []
        for execution in recent_executions:
            exec_list = list(execution)
            if exec_list[2]:
                dt = datetime.fromisoformat(exec_list[2].replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
                exec_list[2] = dt.astimezone(tz).strftime('%Y-%m-%d %I:%M:%S %p')
            if exec_list[3]:
                dt = datetime.fromisoformat(exec_list[3].replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
                exec_list[3] = dt.astimezone(tz).strftime('%Y-%m-%d %I:%M:%S %p')
            executions_list.append(exec_list)

        tasks_with_executions.append({
            "task": task_list,
            "executions": executions_list
        })

    admin_users = db.query(User).filter(
        User.is_admin == True,
        User.email.isnot(None),
        User.email != ""
    ).all()

    employees = db.query(Employee).order_by(Employee.name).all()

    # Add employee name to tasks if applicable
    for item in tasks_with_executions:
        if item['task'][2] == 'employee_tip_report' and len(item['task']) > 17 and item['task'][17]:
            employee_id = item['task'][17]
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            item['employee_name'] = employee.name if employee else None
        else:
            item['employee_name'] = None

    return templates.TemplateResponse(
        "scheduled_tasks/index.html",
        {
            "request": request,
            "current_user": current_user,
            "tasks": tasks_with_executions,
            "admin_users": admin_users,
            "employees": employees
        }
    )

@router.get("/scheduled-tasks/next-runs")
async def get_next_runs(
    schedule_type: str,
    cron_expression: Optional[str] = None,
    interval_value: Optional[int] = None,
    interval_unit: Optional[str] = None,
    starts_at: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    if not current_user or not current_user.is_admin:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    try:
        next_runs = get_next_run_times(
            schedule_type,
            cron_expression,
            interval_value,
            interval_unit,
            starts_at,
            count=5
        )

        if not next_runs:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Could not calculate schedule. Please check your schedule settings."}
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "next_runs": [run.isoformat() for run in next_runs]
            }
        )

    except Exception as e:
        print(f"Error in get_next_runs: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e) if str(e) else "Failed to calculate next run times"}
        )

@router.post("/scheduled-tasks/create")
async def create_scheduled_task(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or not current_user.is_admin:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    form_data = await request.form()
    name = form_data.get("name", "").strip()
    task_type = form_data.get("task_type")
    schedule_type = form_data.get("schedule_type")
    cron_expression = form_data.get("cron_expression", "").strip() if schedule_type == "cron" else None
    interval_value = int(form_data.get("interval_value", 0)) if schedule_type == "interval" else None
    interval_unit = form_data.get("interval_unit") if schedule_type == "interval" else None
    starts_at = form_data.get("starts_at", "").strip() if schedule_type == "interval" else None
    date_range_type = form_data.get("date_range_type") if task_type not in ["backup"] else None
    bypass_opt_in = 1 if form_data.get("bypass_opt_in") == "1" else 0
    employee_id = int(form_data.get("employee_id")) if form_data.get("employee_id") and form_data.get("employee_id").strip() else None

    user_emails = form_data.getlist("user_emails[]")
    additional_email = form_data.get("additional_email", "").strip()

    email_list = [email for email in user_emails if email]
    if additional_email:
        email_list.append(additional_email)

    email_list_json = json.dumps(email_list) if email_list else None

    try:
        next_runs = get_next_run_times(schedule_type, cron_expression, interval_value, interval_unit, starts_at, count=1)
        next_run_at = next_runs[0].isoformat() if next_runs else None

        result = db.execute(text("""
            INSERT INTO scheduled_tasks (
                name, task_type, schedule_type, cron_expression,
                interval_value, interval_unit, starts_at, date_range_type,
                email_list, bypass_opt_in, is_active, next_run_at, employee_id
            ) VALUES (
                :name, :task_type, :schedule_type, :cron_expression,
                :interval_value, :interval_unit, :starts_at, :date_range_type,
                :email_list, :bypass_opt_in, 1, :next_run_at, :employee_id
            )
        """), {
            "name": name,
            "task_type": task_type,
            "schedule_type": schedule_type,
            "cron_expression": cron_expression,
            "interval_value": interval_value,
            "interval_unit": interval_unit,
            "starts_at": starts_at,
            "date_range_type": date_range_type,
            "email_list": email_list_json,
            "bypass_opt_in": bypass_opt_in,
            "next_run_at": next_run_at,
            "employee_id": employee_id
        })
        db.commit()

        task_id = db.execute(text("SELECT last_insert_rowid()")).scalar()

        print(f"✓ Created scheduled task '{name}' (ID: {task_id}) in database")

        add_job_to_scheduler(
            task_id, name, task_type, schedule_type,
            cron_expression, interval_value, interval_unit, starts_at,
            date_range_type, email_list_json, bypass_opt_in, employee_id
        )

        job = scheduler.get_job(f"task_{task_id}")
        if job:
            print(f"✓ Added job to APScheduler - Next run: {job.next_run_time}")
        else:
            print(f"✗ WARNING: Job was not added to APScheduler!")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Scheduled task created successfully"}
        )

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@router.post("/scheduled-tasks/{task_id}/toggle")
async def toggle_scheduled_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or not current_user.is_admin:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    try:
        task = db.execute(text("""
            SELECT * FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id}).fetchone()

        if not task:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Task not found"}
            )

        new_status = 0 if task[12] else 1

        db.execute(text("""
            UPDATE scheduled_tasks
            SET is_active = :is_active
            WHERE id = :task_id
        """), {"is_active": new_status, "task_id": task_id})
        db.commit()

        job_id = f"task_{task_id}"
        if new_status:
            task_dict = db.execute(text("""
                SELECT id, name, task_type, schedule_type, cron_expression,
                       interval_value, interval_unit, starts_at, date_range_type,
                       email_list, bypass_opt_in, employee_id
                FROM scheduled_tasks
                WHERE id = :task_id
            """), {"task_id": task_id}).fetchone()

            add_job_to_scheduler(
                task_dict[0], task_dict[1], task_dict[2], task_dict[3],
                task_dict[4], task_dict[5], task_dict[6], task_dict[7],
                task_dict[8], task_dict[9], task_dict[10], task_dict[11]
            )
        else:
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Task status updated"}
        )

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@router.get("/scheduled-tasks/{task_id}")
async def get_scheduled_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or not current_user.is_admin:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    try:
        task = db.execute(text("""
            SELECT id, name, task_type, schedule_type, cron_expression,
                   interval_value, interval_unit, starts_at, date_range_type,
                   email_list, bypass_opt_in, is_active, employee_id
            FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id}).fetchone()

        if not task:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Task not found"}
            )

        email_list = json.loads(task[9]) if task[9] else []

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "task": {
                    "id": task[0],
                    "name": task[1],
                    "task_type": task[2],
                    "schedule_type": task[3],
                    "cron_expression": task[4],
                    "interval_value": task[5],
                    "interval_unit": task[6],
                    "starts_at": task[7],
                    "date_range_type": task[8],
                    "email_list": email_list,
                    "bypass_opt_in": task[10],
                    "is_active": task[11],
                    "employee_id": task[12]
                }
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@router.put("/scheduled-tasks/{task_id}")
async def update_scheduled_task(
    task_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or not current_user.is_admin:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    try:
        form_data = await request.form()
        name = form_data.get("name", "").strip()
        task_type = form_data.get("task_type")
        schedule_type = form_data.get("schedule_type")
        cron_expression = form_data.get("cron_expression", "").strip() if schedule_type == "cron" else None
        interval_value = int(form_data.get("interval_value", 0)) if schedule_type == "interval" else None
        interval_unit = form_data.get("interval_unit") if schedule_type == "interval" else None
        starts_at = form_data.get("starts_at", "").strip() if schedule_type == "interval" else None
        date_range_type = form_data.get("date_range_type") if task_type not in ["backup"] else None
        bypass_opt_in = 1 if form_data.get("bypass_opt_in") == "1" else 0
        employee_id = int(form_data.get("employee_id")) if form_data.get("employee_id") and form_data.get("employee_id").strip() else None

        # Validation
        if not name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Task name is required"}
            )

        if schedule_type == "cron" and not cron_expression:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Cron expression is required for cron schedule"}
            )

        if schedule_type == "interval" and (not interval_value or interval_value <= 0):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Valid interval value is required for interval schedule"}
            )

        if task_type == "employee_tip_report" and not employee_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Employee selection is required for employee tip reports"}
            )

        user_emails = form_data.getlist("user_emails[]")
        additional_email = form_data.get("additional_email", "").strip()

        email_list = [email for email in user_emails if email]
        if additional_email:
            email_list.append(additional_email)

        email_list_json = json.dumps(email_list) if email_list else None

        # Verify task exists
        existing_task = db.execute(text("""
            SELECT id FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id}).fetchone()

        if not existing_task:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Task not found"}
            )

        next_runs = get_next_run_times(schedule_type, cron_expression, interval_value, interval_unit, starts_at, count=1)
        next_run_at = next_runs[0].isoformat() if next_runs else None

        db.execute(text("""
            UPDATE scheduled_tasks
            SET name = :name,
                task_type = :task_type,
                schedule_type = :schedule_type,
                cron_expression = :cron_expression,
                interval_value = :interval_value,
                interval_unit = :interval_unit,
                starts_at = :starts_at,
                date_range_type = :date_range_type,
                email_list = :email_list,
                bypass_opt_in = :bypass_opt_in,
                next_run_at = :next_run_at,
                employee_id = :employee_id,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :task_id
        """), {
            "name": name,
            "task_type": task_type,
            "schedule_type": schedule_type,
            "cron_expression": cron_expression,
            "interval_value": interval_value,
            "interval_unit": interval_unit,
            "starts_at": starts_at,
            "date_range_type": date_range_type,
            "email_list": email_list_json,
            "bypass_opt_in": bypass_opt_in,
            "next_run_at": next_run_at,
            "employee_id": employee_id,
            "task_id": task_id
        })
        db.commit()

        print(f"✓ Updated task {task_id}: {name}")

        job_id = f"task_{task_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            print(f"  → Removed old scheduler job: {job_id}")

        task = db.execute(text("""
            SELECT is_active FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id}).fetchone()

        if task and task[0]:
            add_job_to_scheduler(
                task_id, name, task_type, schedule_type,
                cron_expression, interval_value, interval_unit, starts_at,
                date_range_type, email_list_json, bypass_opt_in, employee_id
            )
            print(f"  → Re-added scheduler job: {job_id}")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Scheduled task updated successfully"}
        )

    except ValueError as e:
        db.rollback()
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Validation error: {str(e)}"}
        )
    except Exception as e:
        db.rollback()
        print(f"✗ Error updating task {task_id}: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to update task: {str(e)}"}
        )

@router.delete("/scheduled-tasks/{task_id}")
async def delete_scheduled_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or not current_user.is_admin:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    try:
        job_id = f"task_{task_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # Explicitly delete task executions first (safety measure even though CASCADE should handle it)
        db.execute(text("""
            DELETE FROM task_executions WHERE task_id = :task_id
        """), {"task_id": task_id})

        # Delete the scheduled task
        db.execute(text("""
            DELETE FROM scheduled_tasks WHERE id = :task_id
        """), {"task_id": task_id})
        db.commit()

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Task deleted successfully"}
        )

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

def add_job_to_scheduler(
    task_id, name, task_type, schedule_type,
    cron_expression, interval_value, interval_unit, starts_at,
    date_range_type, email_list_json, bypass_opt_in, employee_id=None
):
    """Add a job to the APScheduler"""
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    import pytz

    job_id = f"task_{task_id}"

    print(f"  → Adding job {job_id} to scheduler (type: {task_type}, schedule: {schedule_type})")

    if scheduler.get_job(job_id):
        print(f"  → Job {job_id} already exists, removing old version")
        scheduler.remove_job(job_id)

    if task_type == "tip_report":
        job_func = run_tip_report_task
        job_args = [task_id, name, date_range_type, email_list_json, bypass_opt_in]
    elif task_type == "daily_balance_report":
        job_func = run_daily_balance_report_task
        job_args = [task_id, name, date_range_type, email_list_json, bypass_opt_in]
    elif task_type == "employee_tip_report":
        job_func = run_employee_tip_report_task
        job_args = [task_id, name, date_range_type, email_list_json, bypass_opt_in, employee_id]
    elif task_type == "backup":
        job_func = run_backup_task
        job_args = [task_id, name]
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    if schedule_type == "cron":
        import os
        TIMEZONE = os.getenv('TZ', 'America/Los_Angeles')
        tz = pytz.timezone(TIMEZONE)
        parts = cron_expression.split()
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone=tz
        )
    elif schedule_type == "interval":
        kwargs = {interval_unit: interval_value}

        if starts_at:
            if isinstance(starts_at, str):
                tz = pytz.timezone('America/Los_Angeles')
                start_date = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                if start_date.tzinfo is None:
                    start_date = tz.localize(start_date)
                else:
                    start_date = start_date.astimezone(tz)
                kwargs['start_date'] = start_date

        trigger = IntervalTrigger(**kwargs)
    else:
        raise ValueError(f"Unknown schedule type: {schedule_type}")

    scheduler.add_job(
        job_func,
        trigger=trigger,
        id=job_id,
        name=name,
        args=job_args,
        replace_existing=True
    )

    job = scheduler.get_job(job_id)
    if job and job.next_run_time:
        print(f"  ✓ Job {job_id} scheduled successfully - Next run: {job.next_run_time}")
    else:
        print(f"  ✗ WARNING: Job {job_id} was added but has no next_run_time!")

def cleanup_orphaned_executions():
    """Remove task executions that no longer have a parent scheduled task"""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            DELETE FROM task_executions
            WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
        """))
        db.commit()
        deleted_count = result.rowcount
        if deleted_count > 0:
            print(f"✓ Cleaned up {deleted_count} orphaned task execution(s)")
        return deleted_count
    except Exception as e:
        print(f"✗ Failed to cleanup orphaned executions: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def load_scheduled_tasks():
    """Load all active scheduled tasks from the database and add them to the scheduler"""
    db = SessionLocal()
    try:
        # First, cleanup any orphaned executions
        cleanup_orphaned_executions()

        tasks = db.execute(text("""
            SELECT id, name, task_type, schedule_type, cron_expression,
                   interval_value, interval_unit, starts_at, date_range_type,
                   email_list, bypass_opt_in, employee_id
            FROM scheduled_tasks WHERE is_active = 1
        """)).fetchall()

        loaded_count = 0
        for task in tasks:
            try:
                add_job_to_scheduler(
                    task[0], task[1], task[2], task[3],
                    task[4], task[5], task[6], task[7],
                    task[8], task[9], task[10], task[11]
                )
                loaded_count += 1
                print(f"  ✓ Loaded task: {task[1]} (ID: {task[0]})")
            except Exception as e:
                print(f"  ✗ Failed to load task {task[1]}: {e}")
                import traceback
                traceback.print_exc()

        print(f"✓ Loaded {loaded_count}/{len(tasks)} scheduled tasks into APScheduler")

    except Exception as e:
        print(f"✗ Failed to load scheduled tasks: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

@router.post("/scheduled-tasks/cleanup-orphaned")
async def cleanup_orphaned_executions_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or not current_user.is_admin:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    try:
        deleted_count = cleanup_orphaned_executions()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Cleaned up {deleted_count} orphaned execution(s)",
                "deleted_count": deleted_count
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@router.get("/scheduled-tasks/debug")
async def debug_scheduler(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or not current_user.is_admin:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    try:
        tasks_in_db = db.execute(text("""
            SELECT id, name, task_type, is_active, next_run_at
            FROM scheduled_tasks
        """)).fetchall()

        # Check for orphaned executions
        orphaned_executions = db.execute(text("""
            SELECT COUNT(*) FROM task_executions
            WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)
        """)).scalar()

        jobs_in_scheduler = []
        for job in scheduler.get_jobs():
            jobs_in_scheduler.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "scheduler_running": scheduler.running,
                "tasks_in_database": len(tasks_in_db),
                "jobs_in_scheduler": len(jobs_in_scheduler),
                "orphaned_executions": orphaned_executions,
                "database_tasks": [
                    {
                        "id": t[0],
                        "name": t[1],
                        "type": t[2],
                        "active": bool(t[3]),
                        "next_run_at": t[4]
                    } for t in tasks_in_db
                ],
                "scheduler_jobs": jobs_in_scheduler
            }
        )

    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        )
