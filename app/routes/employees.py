from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from app.database import get_db
from app.models import User, Employee, Position, EmployeePositionSchedule
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    from app.models import DailyEmployeeEntry, DailyFinancialLineItem, ScheduledTask

    employee = db.query(Employee).filter(Employee.slug == slug).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    daily_entries_count = db.query(DailyEmployeeEntry).filter(
        DailyEmployeeEntry.employee_id == employee.id
    ).count()

    financial_items_count = db.query(DailyFinancialLineItem).filter(
        DailyFinancialLineItem.employee_id == employee.id
    ).count()

    scheduled_tasks_count = db.query(ScheduledTask).filter(
        ScheduledTask.employee_id == employee.id
    ).count()

    if daily_entries_count > 0 or financial_items_count > 0 or scheduled_tasks_count > 0:
        error_details = []
        if daily_entries_count > 0:
            error_details.append(f"{daily_entries_count} daily balance entries")
        if financial_items_count > 0:
            error_details.append(f"{financial_items_count} financial line items")
        if scheduled_tasks_count > 0:
            error_details.append(f"{scheduled_tasks_count} scheduled tasks")

        error_message = f"Cannot delete employee. They have {' and '.join(error_details)} associated with them. Please set the employee as inactive instead."

        if request.headers.get("Accept") == "application/json":
            raise HTTPException(status_code=400, detail=error_message)

        employees = db.query(Employee).all()
        return templates.TemplateResponse(
            "employees/list.html",
            {
                "request": request,
                "employees": employees,
                "current_user": current_user,
                "error": error_message
            }
        )

    db.delete(employee)
    db.commit()
    return RedirectResponse(url="/employees", status_code=302)
