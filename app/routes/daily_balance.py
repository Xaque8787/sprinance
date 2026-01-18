from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
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
    finalized: bool = False,
    current_user: User = None,
    source: str = "user"
):
    daily_balance = db.query(DailyBalance).filter(DailyBalance.date == date_obj).first()
    is_new = daily_balance is None

    if not daily_balance:
        daily_balance = DailyBalance(
            date=date_obj,
            day_of_week=day_of_week,
            notes=form_data.get("notes", ""),
            finalized=finalized,
            created_by_user_id=current_user.id if current_user else None,
            created_by_source=source,
            finalized_at=datetime.now() if finalized else None
        )
        db.add(daily_balance)
        db.flush()
    else:
        daily_balance.notes = form_data.get("notes", "")
        was_finalized = daily_balance.finalized
        daily_balance.finalized = finalized

        if current_user:
            daily_balance.edited_by_user_id = current_user.id

        if finalized and not was_finalized:
            daily_balance.finalized_at = datetime.now()
            if not daily_balance.created_by_user_id and current_user:
                daily_balance.created_by_user_id = current_user.id
                daily_balance.created_by_source = source

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
        employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if not employee:
            continue

        tip_values = {}

        for req in employee.position.tip_requirements:
            if not req.no_input and not req.is_total:
                field_key = f"tip_{req.field_name}_{emp_id}"
                value = float(form_data.get(field_key, 0.0))
                tip_values[req.field_name] = value

                if req.apply_to_revenue and value != 0:
                    max_order += 1
                    tip_line_item = DailyFinancialLineItem(
                        daily_balance_id=daily_balance.id,
                        template_id=None,
                        name=f"{employee.display_name} - {req.name}",
                        category="revenue",
                        value=value if not req.revenue_is_deduction else -value,
                        display_order=max_order,
                        is_employee_tip=True,
                        employee_id=emp_id
                    )
                    db.add(tip_line_item)

                if req.apply_to_expense and value != 0:
                    max_order += 1
                    tip_line_item = DailyFinancialLineItem(
                        daily_balance_id=daily_balance.id,
                        template_id=None,
                        name=f"{employee.display_name} - {req.name}",
                        category="expense",
                        value=value if not req.expense_is_deduction else -value,
                        display_order=max_order,
                        is_employee_tip=True,
                        employee_id=emp_id
                    )
                    db.add(tip_line_item)

            elif req.is_total:
                total = 0
                for other_req in employee.position.tip_requirements:
                    if not other_req.no_input and not other_req.is_total and not other_req.record_data:
                        field_key = f"tip_{other_req.field_name}_{emp_id}"
                        value = float(form_data.get(field_key, 0.0))
                        if other_req.is_deduction:
                            total -= value
                        else:
                            total += value
                tip_values[req.field_name] = total

        entry = DailyEmployeeEntry(
            daily_balance_id=daily_balance.id,
            employee_id=emp_id,
            tip_values=tip_values
        )
        db.add(entry)

    db.commit()
    db.refresh(daily_balance)

    return daily_balance

def attach_display_orders_to_employee(emp, db):
    requirements_with_order = sorted(
        emp.position.tip_requirements,
        key=lambda req: req.display_order
    )
    emp.position.tip_requirements = requirements_with_order

def serialize_employee(emp, db):
    attach_display_orders_to_employee(emp, db)

    return {
        "id": emp.id,
        "name": emp.name,
        "display_name": emp.display_name,
        "position": {
            "id": emp.position.id,
            "name": emp.position.name,
            "tip_requirements": [
                {
                    "id": req.id,
                    "name": req.name,
                    "field_name": req.field_name,
                    "display_order": req.display_order,
                    "no_input": req.no_input,
                    "is_total": req.is_total,
                    "is_deduction": req.is_deduction,
                    "no_null_value": req.no_null_value,
                    "apply_to_revenue": req.apply_to_revenue,
                    "revenue_is_deduction": req.revenue_is_deduction,
                    "apply_to_expense": req.apply_to_expense,
                    "expense_is_deduction": req.expense_is_deduction,
                    "record_data": req.record_data,
                    "include_in_payroll_summary": req.include_in_payroll_summary
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

    for emp in working_employees:
        attach_display_orders_to_employee(emp, db)

    all_employees_serialized = [serialize_employee(emp, db) for emp in all_employees]
    working_employee_ids = [emp.id for emp in working_employees]

    templates_list = db.query(FinancialLineItemTemplate).order_by(
        FinancialLineItemTemplate.category,
        FinancialLineItemTemplate.display_order
    ).all()

    financial_line_items = {}
    if daily_balance:
        for item in daily_balance.financial_line_items:
            financial_line_items[f"{item.category}_{item.template_id or item.id}"] = item

    from datetime import timedelta
    previous_date = target_date - timedelta(days=1)
    previous_daily_balance = db.query(DailyBalance).filter(DailyBalance.date == previous_date).first()

    previous_ending_till = 0.0
    if previous_daily_balance:
        for item in previous_daily_balance.financial_line_items:
            if item.template_id:
                template = db.query(FinancialLineItemTemplate).filter(
                    FinancialLineItemTemplate.id == item.template_id
                ).first()
                if template and template.is_ending_till:
                    previous_ending_till = item.value
                    break

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
            "financial_line_items": financial_line_items,
            "previous_ending_till": previous_ending_till
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
    save_daily_balance_data(db, date_obj, day_of_week, form_data, finalized=False, current_user=current_user, source="user")

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
    daily_balance = save_daily_balance_data(db, date_obj, day_of_week, form_data, finalized=True, current_user=current_user, source="user")

    generate_daily_balance_csv(daily_balance, daily_balance.employee_entries, current_user=current_user, source="user")

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

    # Construct the filepath using year/month directory structure
    year = str(date_obj.year)
    month = f"{date_obj.month:02d}"
    filename = f"{date_obj}-daily-balance.csv"
    filepath = os.path.join("data", "reports", "daily_report", year, month, filename)

    if not os.path.exists(filepath):
        generate_daily_balance_csv(daily_balance, daily_balance.employee_entries)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="CSV file not found")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )
