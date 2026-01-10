from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date as date_cls, datetime
from typing import List, Optional
import os
from app.database import get_db
from app.models import User, Employee, DailyBalance, DailyEmployeeEntry, FinancialLineItemTemplate, DailyFinancialLineItem
from app.auth.jwt_handler import get_current_user
from app.utils.csv_generator import generate_daily_balance_csv

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def save_daily_balance_data(
    db: Session,
    date_obj: date_cls,
    day_of_week: str,
    form_data: dict,
    finalized: bool = False
):
    daily_balance = db.query(DailyBalance).filter(DailyBalance.date == date_obj).first()

    if not daily_balance:
        daily_balance = DailyBalance(
            date=date_obj,
            day_of_week=day_of_week,
            notes=form_data.get("notes", ""),
            finalized=finalized
        )
        db.add(daily_balance)
        db.flush()
    else:
        daily_balance.notes = form_data.get("notes", "")
        daily_balance.finalized = finalized

    for entry in daily_balance.financial_line_items:
        db.delete(entry)
    db.flush()

    financial_templates = db.query(FinancialLineItemTemplate).order_by(
        FinancialLineItemTemplate.display_order
    ).all()

    for template in financial_templates:
        value_key = f"financial_item_{template.id}"
        value = float(form_data.get(value_key, 0.0))

        line_item = DailyFinancialLineItem(
            daily_balance_id=daily_balance.id,
            template_id=template.id,
            name=template.name,
            category=template.category,
            value=value,
            display_order=template.display_order,
            is_employee_tip=False
        )
        db.add(line_item)

    employee_ids = form_data.getlist("employee_ids")
    employee_ids = [int(emp_id) for emp_id in employee_ids if emp_id]

    for entry in daily_balance.employee_entries:
        db.delete(entry)
    db.flush()

    max_order = len(financial_templates)

    for emp_id in employee_ids:
        bank_card_sales = float(form_data.get(f"bank_card_sales_{emp_id}", 0.0))
        bank_card_tips = float(form_data.get(f"bank_card_tips_{emp_id}", 0.0))
        cash_tips = float(form_data.get(f"cash_tips_{emp_id}", 0.0))
        total_sales = float(form_data.get(f"total_sales_{emp_id}", 0.0))
        adjustments = float(form_data.get(f"adjustments_{emp_id}", 0.0))
        tips_on_paycheck = float(form_data.get(f"tips_on_paycheck_{emp_id}", 0.0))

        calculated_take_home = bank_card_tips + cash_tips + adjustments - tips_on_paycheck

        entry = DailyEmployeeEntry(
            daily_balance_id=daily_balance.id,
            employee_id=emp_id,
            bank_card_sales=bank_card_sales,
            bank_card_tips=bank_card_tips,
            cash_tips=cash_tips,
            total_sales=total_sales,
            adjustments=adjustments,
            tips_on_paycheck=tips_on_paycheck,
            calculated_take_home=calculated_take_home
        )
        db.add(entry)

        if tips_on_paycheck > 0:
            employee = db.query(Employee).filter(Employee.id == emp_id).first()
            if employee:
                max_order += 1
                tip_line_item = DailyFinancialLineItem(
                    daily_balance_id=daily_balance.id,
                    template_id=None,
                    name=f"{employee.name} - Tips on Paycheck",
                    category="revenue",
                    value=tips_on_paycheck,
                    display_order=max_order,
                    is_employee_tip=True,
                    employee_id=emp_id
                )
                db.add(tip_line_item)

    db.commit()
    db.refresh(daily_balance)

    return daily_balance

def serialize_employee(emp):
    return {
        "id": emp.id,
        "name": emp.name,
        "position": {
            "id": emp.position.id,
            "name": emp.position.name,
            "tip_requirements": [
                {
                    "id": req.id,
                    "name": req.name,
                    "field_name": req.field_name
                } for req in emp.position.tip_requirements
            ]
        }
    }

@router.get("/daily-balance", response_class=HTMLResponse)
async def daily_balance_page(
    request: Request,
    selected_date: Optional[str] = None,
    date: Optional[str] = None,
    edit: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    date_param = selected_date or date
    if date_param:
        target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
    else:
        target_date = date_cls.today()

    day_of_week = DAYS_OF_WEEK[target_date.weekday()]

    daily_balance = db.query(DailyBalance).filter(DailyBalance.date == target_date).first()

    all_employees = db.query(Employee).all()
    scheduled_employees = [emp for emp in all_employees if day_of_week in emp.scheduled_days]

    employee_entries = {}
    if daily_balance:
        for entry in daily_balance.employee_entries:
            employee_entries[entry.employee_id] = entry

    working_employees = []
    if daily_balance:
        working_employees = [entry.employee for entry in daily_balance.employee_entries]
    else:
        working_employees = scheduled_employees

    all_employees_serialized = [serialize_employee(emp) for emp in all_employees]
    working_employee_ids = [emp.id for emp in working_employees]

    templates_list = db.query(FinancialLineItemTemplate).order_by(
        FinancialLineItemTemplate.category,
        FinancialLineItemTemplate.display_order
    ).all()

    financial_line_items = {}
    if daily_balance:
        for item in daily_balance.financial_line_items:
            financial_line_items[f"{item.category}_{item.template_id or item.id}"] = item

    return templates.TemplateResponse(
        "daily_balance/form.html",
        {
            "request": request,
            "current_user": current_user,
            "target_date": target_date,
            "day_of_week": day_of_week,
            "daily_balance": daily_balance,
            "all_employees": all_employees_serialized,
            "working_employees": working_employees,
            "working_employee_ids": working_employee_ids,
            "employee_entries": employee_entries,
            "scheduled_employees": scheduled_employees,
            "edit_mode": edit,
            "financial_templates": templates_list,
            "financial_line_items": financial_line_items
        }
    )

@router.post("/daily-balance/save")
async def save_daily_balance_route(
    request: Request,
    target_date: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    day_of_week = DAYS_OF_WEEK[date_obj.weekday()]

    form_data = await request.form()
    save_daily_balance_data(db, date_obj, day_of_week, form_data, finalized=False)

    return RedirectResponse(url=f"/daily-balance?selected_date={target_date}", status_code=302)

@router.post("/daily-balance/finalize")
async def finalize_daily_balance_route(
    request: Request,
    target_date: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    day_of_week = DAYS_OF_WEEK[date_obj.weekday()]

    form_data = await request.form()
    daily_balance = save_daily_balance_data(db, date_obj, day_of_week, form_data, finalized=True)

    generate_daily_balance_csv(daily_balance, daily_balance.employee_entries)

    return RedirectResponse(url=f"/daily-balance?selected_date={target_date}", status_code=302)

@router.get("/daily-balance/export")
async def export_daily_balance(
    date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    daily_balance = db.query(DailyBalance).filter(DailyBalance.date == date_obj).first()

    if not daily_balance or not daily_balance.finalized:
        raise HTTPException(status_code=404, detail="Finalized report not found for this date")

    filename = f"{date_obj}-daily-balance.csv"
    filepath = os.path.join("data/reports", filename)

    if not os.path.exists(filepath):
        generate_daily_balance_csv(daily_balance, daily_balance.employee_entries)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="CSV file not found")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )
