from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db, database_exists
from app.models import User
from app.auth.jwt_handler import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user_from_cookie
)
from app.utils.slugify import create_slug, ensure_unique_slug
from app.utils.version import check_version

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/", status_code=302)

    if not database_exists() or db.query(User).count() == 0:
        return templates.TemplateResponse("setup.html", {"request": request})

    version, update_available = check_version()
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,
            "version": version,
            "update_available": update_available
        }
    )

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, username, password)
    if not user:
        version, update_available = check_version()
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password",
                "version": version,
                "update_available": update_available
            }
        )

    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.post("/setup")
async def setup_admin(
    request: Request,
    username: str = Form(...),
    email: str = Form(None),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="Setup already completed")

    slug = ensure_unique_slug(db, User, create_slug(username))

    new_user = User(
        username=username,
        password_hash=get_password_hash(password),
        slug=slug,
        email=email if email else None,
        is_admin=True
    )
    db.add(new_user)
    db.commit()

    access_token = create_access_token(data={"sub": new_user.username})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response
