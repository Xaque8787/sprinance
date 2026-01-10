from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Employee, Position
from app.auth.jwt_handler import get_current_user
from app.utils.slugify import create_slug, ensure_unique_slug

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/employees", response_class=HTMLResponse)
async def employees_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employees = db.query(Employee).all()
    return templates.TemplateResponse(
        "employees/list.html",
        {"request": request, "employees": employees, "current_user": current_user}
    )

@router.get("/employees/new", response_class=HTMLResponse)
async def new_employee_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    positions = db.query(Position).all()
    return templates.TemplateResponse(
        "employees/form.html",
        {"request": request, "employee": None, "positions": positions, "current_user": current_user}
    )

@router.post("/employees/new")
async def create_employee(
    request: Request,
    name: str = Form(...),
    position_id: int = Form(...),
    scheduled_days: List[str] = Form([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slug = ensure_unique_slug(db, Employee, create_slug(name))

    new_employee = Employee(
        name=name,
        slug=slug,
        position_id=position_id,
        scheduled_days=scheduled_days
    )
    db.add(new_employee)
    db.commit()

    return RedirectResponse(url="/employees", status_code=302)

@router.get("/employees/{slug}", response_class=HTMLResponse)
async def employee_detail(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.slug == slug).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return templates.TemplateResponse(
        "employees/detail.html",
        {"request": request, "employee": employee, "current_user": current_user}
    )

@router.get("/employees/{slug}/edit", response_class=HTMLResponse)
async def edit_employee_page(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.slug == slug).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    positions = db.query(Position).all()
    return templates.TemplateResponse(
        "employees/form.html",
        {"request": request, "employee": employee, "positions": positions, "current_user": current_user}
    )

@router.post("/employees/{slug}/edit")
async def update_employee(
    slug: str,
    request: Request,
    name: str = Form(...),
    position_id: int = Form(...),
    scheduled_days: List[str] = Form([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.slug == slug).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.name = name
    employee.position_id = position_id
    employee.scheduled_days = scheduled_days

    db.commit()
    return RedirectResponse(url=f"/employees/{slug}", status_code=302)

@router.post("/employees/{slug}/delete")
async def delete_employee(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.slug == slug).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()
    return RedirectResponse(url="/employees", status_code=302)
