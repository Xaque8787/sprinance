from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Setting
from app.auth.jwt_handler import get_current_admin_user, get_password_hash
from app.utils.slugify import create_slug, ensure_unique_slug
from app.utils.backup import create_backup, list_backups, delete_backup, get_backup_path, restore_backup, get_backup_retention_count, cleanup_old_backups

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
