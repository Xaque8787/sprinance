from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from app.database import init_db, get_db
from app.models import User, Position, TipEntryRequirement, Setting
from app.auth.jwt_handler import get_current_user_from_cookie
from app.routes import auth, admin, employees, daily_balance, positions, tip_requirements, reports, financial_items, scheduled_tasks, checks_efts
from app.utils.slugify import create_slug
from app.utils.version import check_version
from app.utils.logging_config import setup_error_logging
from app.scheduler import start_scheduler, shutdown_scheduler
import logging

app = FastAPI(title="Internal Management System")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

def format_decimal(value, decimals=2):
    """Format a number to a fixed number of decimal places."""
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return value

templates.env.filters["format_decimal"] = format_decimal

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(employees.router)
app.include_router(daily_balance.router)
app.include_router(positions.router)
app.include_router(tip_requirements.router)
app.include_router(reports.router)
app.include_router(financial_items.router)
app.include_router(scheduled_tasks.router)
app.include_router(checks_efts.router)

def initialize_predefined_data():
    # No longer creating hardcoded positions and tip requirements
    # Users will create these manually via the UI
    pass

def initialize_default_settings():
    """Initialize default settings if they don't exist."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        default_settings = [
            ("backup_retention_count", "7", "Number of database backups to keep"),
            ("log_max_size_mb", "10", "Maximum size of log file in MB before rotation"),
            ("log_backup_count", "5", "Number of rotated log files to keep"),
            ("log_capture_info", "0", "Capture INFO level logs"),
            ("log_capture_debug", "0", "Capture DEBUG level logs"),
        ]

        for key, value, description in default_settings:
            existing = db.query(Setting).filter(Setting.key == key).first()
            if not existing:
                db.add(Setting(key=key, value=value, description=description))

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error initializing default settings: {e}")
    finally:
        db.close()

def initialize_error_logging():
    """Initialize error logging with settings from database."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        log_max_size = db.query(Setting).filter(Setting.key == "log_max_size_mb").first()
        log_backup_count = db.query(Setting).filter(Setting.key == "log_backup_count").first()
        log_capture_info = db.query(Setting).filter(Setting.key == "log_capture_info").first()
        log_capture_debug = db.query(Setting).filter(Setting.key == "log_capture_debug").first()

        max_bytes = int(log_max_size.value) * 1024 * 1024 if log_max_size else 10485760
        backup_count = int(log_backup_count.value) if log_backup_count else 5

        capture_info = log_capture_info and log_capture_info.value == "1"
        capture_debug = log_capture_debug and log_capture_debug.value == "1"

        if capture_debug:
            log_level = logging.DEBUG
        elif capture_info:
            log_level = logging.INFO
        else:
            log_level = logging.WARNING

        setup_error_logging(max_bytes=max_bytes, backup_count=backup_count, log_level=log_level)
        logging.info("Error logging initialized successfully")
    except Exception as e:
        print(f"Error initializing logging: {e}")
        setup_error_logging()
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    init_db()
    initialize_predefined_data()
    initialize_default_settings()
    initialize_error_logging()
    start_scheduler()
    from app.routes.scheduled_tasks import load_scheduled_tasks
    load_scheduled_tasks()

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_scheduler()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)

    if not user:
        return RedirectResponse(url="/login", status_code=302)

    today = date.today()
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_of_week = days_of_week[today.weekday()]

    version, update_available = check_version()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_user": user,
            "current_date": today,
            "day_of_week": day_of_week,
            "version": version,
            "update_available": update_available
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5710)
