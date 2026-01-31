from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from app.database import get_db
from app.models import User, Employee, Position, EmployeePositionSchedule
from app.auth.jwt_handler import get_current_admin_user
from app.utils.slugify import create_slug, ensure_unique_slug

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/employees", response_class=HTMLResponse)
async def employees_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
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
    current_user: User = Depends(get_current_admin_user)
):
    positions = db.query(Position).all()
    positions_data = [{"id": p.id, "name": p.name} for p in positions]
    return templates.TemplateResponse(
        "employees/form.html",
        {"request": request, "employee": None, "positions": positions_data, "current_user": current_user}
    )

@router.post("/employees/new")
async def create_employee(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    is_active: Optional[str] = Form(None),
    position_schedules: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    schedules_data = json.loads(position_schedules)

    if not schedules_data or len(schedules_data) == 0:
        raise HTTPException(status_code=400, detail="At least one position must be assigned")

    full_name = f"{last_name}, {first_name}"
    slug = ensure_unique_slug(db, Employee, create_slug(full_name))

    new_employee = Employee(
        name=full_name,
        first_name=first_name,
        last_name=last_name,
        slug=slug,
        is_active=(is_active == "true" if is_active else True)
    )
    db.add(new_employee)
    db.flush()

    for schedule in schedules_data:
        new_schedule = EmployeePositionSchedule(
            employee_id=new_employee.id,
            position_id=schedule['position_id'],
            days_of_week=schedule.get('days_of_week', [])
        )
        db.add(new_schedule)

    db.commit()
    return RedirectResponse(url="/employees", status_code=302)

@router.get("/employees/{slug}", response_class=HTMLResponse)
async def employee_detail(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
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
    current_user: User = Depends(get_current_admin_user)
):
    employee = db.query(Employee).filter(Employee.slug == slug).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    positions = db.query(Position).all()
    positions_data = [{"id": p.id, "name": p.name} for p in positions]

    employee_schedules = [
        {
            "position_id": schedule.position_id,
            "days_of_week": schedule.days_of_week or []
        }
        for schedule in employee.position_schedules
    ]

    return templates.TemplateResponse(
        "employees/form.html",
        {
            "request": request,
            "employee": employee,
            "positions": positions_data,
            "employee_schedules": employee_schedules,
            "current_user": current_user
        }
    )

@router.post("/employees/{slug}/edit")
async def update_employee(
    slug: str,
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    is_active: Optional[str] = Form(None),
    position_schedules: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    employee = db.query(Employee).filter(Employee.slug == slug).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    schedules_data = json.loads(position_schedules)

    if not schedules_data or len(schedules_data) == 0:
        raise HTTPException(status_code=400, detail="At least one position must be assigned")

    full_name = f"{last_name}, {first_name}"
    employee.name = full_name
    employee.first_name = first_name
    employee.last_name = last_name
    employee.is_active = (is_active == "true" if is_active else False)

    db.query(EmployeePositionSchedule).filter(
        EmployeePositionSchedule.employee_id == employee.id
    ).delete()

    for schedule in schedules_data:
        new_schedule = EmployeePositionSchedule(
            employee_id=employee.id,
            position_id=schedule['position_id'],
            days_of_week=schedule.get('days_of_week', [])
        )
        db.add(new_schedule)

    db.commit()
    return RedirectResponse(url=f"/employees/{slug}", status_code=302)

@router.post("/employees/{slug}/delete")
async def delete_employee(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    from app.models import DailyEmployeeEntry, DailyFinancialLineItem, ScheduledTask, Position

    employee = db.query(Employee).filter(Employee.slug == slug).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    daily_entries = db.query(DailyEmployeeEntry).filter(
        DailyEmployeeEntry.employee_id == employee.id
    ).all()

    for entry in daily_entries:
        if not entry.employee_name_snapshot:
            entry.employee_name_snapshot = employee.display_name
        if not entry.position_name_snapshot and entry.position_id:
            position = db.query(Position).filter(Position.id == entry.position_id).first()
            if position:
                entry.position_name_snapshot = position.name
        entry.employee_id = None

    financial_items = db.query(DailyFinancialLineItem).filter(
        DailyFinancialLineItem.employee_id == employee.id
    ).all()

    for item in financial_items:
        if not item.employee_name_snapshot:
            item.employee_name_snapshot = employee.display_name
        item.employee_id = None

    scheduled_tasks = db.query(ScheduledTask).filter(
        ScheduledTask.employee_id == employee.id
    ).all()

    for task in scheduled_tasks:
        task.employee_id = None

    db.delete(employee)
    db.commit()
    return RedirectResponse(url="/employees", status_code=302)
