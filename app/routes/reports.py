from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional
import os
from app.database import get_db
from app.models import User, DailyBalance, Employee, DailyEmployeeEntry
from app.auth.jwt_handler import get_current_user
from app.utils.csv_generator import generate_tip_report_csv

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/reports")
async def reports_index(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "reports/index.html",
        {
            "request": request,
            "current_user": current_user
        }
    )

@router.get("/reports/daily-balance")
async def daily_balance_reports_page(
    request: Request,
    month: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    if month:
        try:
            target_date = datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            target_date = date.today().replace(day=1)
    else:
        target_date = date.today().replace(day=1)

    month_start = target_date.replace(day=1)
    next_month = month_start + relativedelta(months=1)
    prev_month = month_start - relativedelta(months=1)

    finalized_reports = db.query(DailyBalance).filter(
        DailyBalance.date >= month_start,
        DailyBalance.date < next_month,
        DailyBalance.finalized == True
    ).order_by(DailyBalance.date.desc()).all()

    return templates.TemplateResponse(
        "reports/daily_balance_list.html",
        {
            "request": request,
            "current_user": current_user,
            "current_month": target_date,
            "prev_month": prev_month,
            "next_month": next_month,
            "finalized_reports": finalized_reports,
            "is_current_month": target_date.year == date.today().year and target_date.month == date.today().month
        }
    )

@router.get("/reports/tip-report")
async def tip_report_page(
    request: Request,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    employees_query = db.query(Employee)

    if search:
        employees_query = employees_query.filter(Employee.name.ilike(f"%{search}%"))

    employees = employees_query.order_by(Employee.name).all()

    for emp in employees:
        entry_count = db.query(DailyEmployeeEntry).filter(
            DailyEmployeeEntry.employee_id == emp.id
        ).join(DailyBalance).filter(
            DailyBalance.finalized == True
        ).count()
        emp.entry_count = entry_count

    return templates.TemplateResponse(
        "reports/tip_report_list.html",
        {
            "request": request,
            "current_user": current_user,
            "employees": employees,
            "search": search or ""
        }
    )

@router.get("/reports/tip-report/employee/{employee_id}")
async def employee_tip_report(
    request: Request,
    employee_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    month: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return RedirectResponse(url="/reports/tip-report", status_code=303)

    if month:
        try:
            target_date = datetime.strptime(month, "%Y-%m").date()
            start_date_obj = target_date.replace(day=1)
            end_date_obj = start_date_obj + relativedelta(months=1) - relativedelta(days=1)
        except ValueError:
            target_date = date.today().replace(day=1)
            start_date_obj = target_date
            end_date_obj = start_date_obj + relativedelta(months=1) - relativedelta(days=1)
    elif start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            target_date = start_date_obj
        except ValueError:
            target_date = date.today().replace(day=1)
            start_date_obj = target_date
            end_date_obj = start_date_obj + relativedelta(months=1) - relativedelta(days=1)
    else:
        target_date = date.today().replace(day=1)
        start_date_obj = target_date
        end_date_obj = start_date_obj + relativedelta(months=1) - relativedelta(days=1)

    entries = db.query(DailyEmployeeEntry).filter(
        DailyEmployeeEntry.employee_id == employee_id
    ).join(DailyBalance).filter(
        DailyBalance.finalized == True,
        DailyBalance.date >= start_date_obj,
        DailyBalance.date <= end_date_obj
    ).order_by(DailyBalance.date.desc()).all()

    total_bank_card_tips = sum(entry.bank_card_tips or 0 for entry in entries)
    total_cash_tips = sum(entry.cash_tips or 0 for entry in entries)
    total_adjustments = sum(entry.adjustments or 0 for entry in entries)
    total_take_home = sum(entry.calculated_take_home or 0 for entry in entries)

    prev_month = target_date - relativedelta(months=1)
    next_month = target_date + relativedelta(months=1)

    return templates.TemplateResponse(
        "reports/employee_tip_detail.html",
        {
            "request": request,
            "current_user": current_user,
            "employee": employee,
            "entries": entries,
            "start_date": start_date_obj,
            "end_date": end_date_obj,
            "current_month": target_date,
            "prev_month": prev_month,
            "next_month": next_month,
            "total_bank_card_tips": total_bank_card_tips,
            "total_cash_tips": total_cash_tips,
            "total_adjustments": total_adjustments,
            "total_take_home": total_take_home,
            "is_custom_range": bool(start_date and end_date)
        }
    )

@router.get("/reports/tip-report/export")
async def export_tip_report(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return RedirectResponse(url="/reports/tip-report", status_code=303)

    filename = generate_tip_report_csv(db, start_date_obj, end_date_obj)
    filepath = os.path.join("data/reports", filename)

    if not os.path.exists(filepath):
        return RedirectResponse(url="/reports/tip-report", status_code=303)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )
