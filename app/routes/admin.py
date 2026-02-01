from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Setting
from app.auth.jwt_handler import get_current_admin_user, get_password_hash
from app.utils.slugify import create_slug, ensure_unique_slug
from app.utils.backup import create_backup, list_backups, delete_backup, get_backup_path, restore_backup, get_backup_retention_count, cleanup_old_backups
from app.utils.logging_config import get_log_files, read_log_file, get_log_stats, clear_log_file

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    users = db.query(User).all()
    backups = list_backups()
    backup_retention_count = get_backup_retention_count()
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "users": users,
            "backups": backups,
            "backup_retention_count": backup_retention_count,
            "current_user": current_user
        }
    )

@router.get("/admin/users/new", response_class=HTMLResponse)
async def new_user_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return templates.TemplateResponse(
        "admin/user_form.html",
        {"request": request, "user": None, "current_user": current_user}
    )

@router.post("/admin/users/new")
async def create_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(None),
    password: str = Form(...),
    is_admin: bool = Form(False),
    opt_in_daily_reports: bool = Form(False),
    opt_in_tip_reports: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    slug = ensure_unique_slug(db, User, create_slug(username))

    new_user = User(
        username=username,
        password_hash=get_password_hash(password),
        slug=slug,
        email=email if email else None,
        is_admin=is_admin,
        opt_in_daily_reports=opt_in_daily_reports,
        opt_in_tip_reports=opt_in_tip_reports
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/admin", status_code=302)

@router.get("/admin/users/{slug}/edit", response_class=HTMLResponse)
async def edit_user_page(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.slug == slug).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(
        "admin/user_form.html",
        {"request": request, "user": user, "current_user": current_user}
    )

@router.post("/admin/users/{slug}/edit")
async def update_user(
    slug: str,
    request: Request,
    username: str = Form(...),
    email: str = Form(None),
    password: str = Form(None),
    is_admin: bool = Form(False),
    opt_in_daily_reports: bool = Form(False),
    opt_in_tip_reports: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.slug == slug).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = username
    user.email = email if email else None
    if password:
        user.password_hash = get_password_hash(password)
    user.is_admin = is_admin
    user.opt_in_daily_reports = opt_in_daily_reports
    user.opt_in_tip_reports = opt_in_tip_reports

    db.commit()
    return RedirectResponse(url="/admin", status_code=302)

@router.post("/admin/users/{slug}/delete")
async def delete_user(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.slug == slug).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(user)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)

@router.post("/admin/backups/create")
async def create_database_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    try:
        create_backup()
        return RedirectResponse(url="/admin", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/backups/{filename}/download")
async def download_backup(
    filename: str,
    current_user: User = Depends(get_current_admin_user)
):
    try:
        filepath = get_backup_path(filename)
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream"
        )
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/admin/backups/{filename}/delete")
async def delete_database_backup(
    filename: str,
    current_user: User = Depends(get_current_admin_user)
):
    success = delete_backup(filename)
    if not success:
        raise HTTPException(status_code=404, detail="Backup not found")
    return RedirectResponse(url="/admin", status_code=302)

@router.post("/admin/backups/{filename}/restore")
async def restore_database_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    try:
        db.close()

        restore_backup(filename)

        return RedirectResponse(url="/admin?restored=true", status_code=302)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/settings/backup-retention")
async def update_backup_retention(
    retention_count: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    try:
        if retention_count < 1:
            raise HTTPException(status_code=400, detail="Retention count must be at least 1")

        setting = db.query(Setting).filter(Setting.key == "backup_retention_count").first()

        if setting:
            setting.value = str(retention_count)
        else:
            setting = Setting(
                key="backup_retention_count",
                value=str(retention_count),
                description="Number of database backups to keep"
            )
            db.add(setting)

        db.commit()

        cleanup_old_backups(retention_count)

        return RedirectResponse(url="/admin?settings_updated=true", status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/error-logs", response_class=HTMLResponse)
async def view_error_logs(
    request: Request,
    max_lines: int = 500,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    log_files = get_log_files()
    log_stats = get_log_stats()

    log_lines = []
    if log_files:
        log_lines = read_log_file(log_files[0], max_lines)

    log_max_size = db.query(Setting).filter(Setting.key == "log_max_size_mb").first()
    log_backup_count = db.query(Setting).filter(Setting.key == "log_backup_count").first()
    log_capture_info = db.query(Setting).filter(Setting.key == "log_capture_info").first()
    log_capture_debug = db.query(Setting).filter(Setting.key == "log_capture_debug").first()

    return templates.TemplateResponse(
        "admin/error_logs.html",
        {
            "request": request,
            "log_lines": log_lines,
            "log_stats": log_stats,
            "log_max_size_mb": int(log_max_size.value) if log_max_size else 10,
            "log_backup_count": int(log_backup_count.value) if log_backup_count else 5,
            "log_capture_info": int(log_capture_info.value) if log_capture_info else 0,
            "log_capture_debug": int(log_capture_debug.value) if log_capture_debug else 0,
            "current_user": current_user
        }
    )

@router.post("/admin/settings/log-rotation")
async def update_log_rotation(
    log_max_size_mb: int = Form(...),
    log_backup_count: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    try:
        if log_max_size_mb < 1 or log_max_size_mb > 100:
            raise HTTPException(status_code=400, detail="Log size must be between 1 and 100 MB")

        if log_backup_count < 1 or log_backup_count > 20:
            raise HTTPException(status_code=400, detail="Backup count must be between 1 and 20")

        size_setting = db.query(Setting).filter(Setting.key == "log_max_size_mb").first()
        if size_setting:
            size_setting.value = str(log_max_size_mb)
        else:
            db.add(Setting(
                key="log_max_size_mb",
                value=str(log_max_size_mb),
                description="Maximum size of log file in MB before rotation"
            ))

        count_setting = db.query(Setting).filter(Setting.key == "log_backup_count").first()
        if count_setting:
            count_setting.value = str(log_backup_count)
        else:
            db.add(Setting(
                key="log_backup_count",
                value=str(log_backup_count),
                description="Number of rotated log files to keep"
            ))

        db.commit()

        return RedirectResponse(url="/admin/error-logs?settings_updated=true", status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/settings/log-levels")
async def update_log_levels(
    log_capture_info: bool = Form(False),
    log_capture_debug: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    from app.utils.logging_config import reconfigure_logging

    try:
        info_setting = db.query(Setting).filter(Setting.key == "log_capture_info").first()
        if info_setting:
            info_setting.value = "1" if log_capture_info else "0"
        else:
            db.add(Setting(
                key="log_capture_info",
                value="1" if log_capture_info else "0",
                description="Capture INFO level logs"
            ))

        debug_setting = db.query(Setting).filter(Setting.key == "log_capture_debug").first()
        if debug_setting:
            debug_setting.value = "1" if log_capture_debug else "0"
        else:
            db.add(Setting(
                key="log_capture_debug",
                value="1" if log_capture_debug else "0",
                description="Capture DEBUG level logs"
            ))

        db.commit()

        reconfigure_logging()

        return RedirectResponse(url="/admin/error-logs?levels_updated=true", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/logs/clear")
async def clear_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    try:
        success = clear_log_file()
        if success:
            return RedirectResponse(url="/admin/error-logs?cleared=true", status_code=302)
        else:
            raise HTTPException(status_code=404, detail="Log file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
