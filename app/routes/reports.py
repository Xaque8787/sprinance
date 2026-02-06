from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional, List
import os
import re
from app.database import get_db
from app.models import User, DailyBalance, Employee, DailyEmployeeEntry
from app.auth.jwt_handler import get_current_user
from app.utils.csv_generator import generate_tip_report_csv, generate_consolidated_daily_balance_csv, generate_employee_tip_report_csv
from app.utils.csv_reader import get_saved_tip_reports, parse_tip_report_csv, get_saved_daily_balance_reports, parse_daily_balance_csv
from app.utils.email import send_report_emails

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def format_decimal(value, decimals=2):
    """Format a number to a fixed number of decimal places."""
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return value

templates.env.filters["format_decimal"] = format_decimal

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

    saved_reports = get_saved_daily_balance_reports(limit=4)

    return templates.TemplateResponse(
        "reports/daily_balance_list.html",
        {
            "request": request,
            "current_user": current_user,
            "current_month": target_date,
            "prev_month": prev_month,
            "next_month": next_month,
            "finalized_reports": finalized_reports,
            "saved_reports": saved_reports,
            "is_current_month": target_date.year == date.today().year and target_date.month == date.today().month
        }
    )

@router.get("/reports/daily-balance/export")
async def export_consolidated_daily_balance(
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
        return RedirectResponse(url="/reports/daily-balance", status_code=303)

    filename = generate_consolidated_daily_balance_csv(db, start_date_obj, end_date_obj, current_user=current_user, source="user")

    year = str(start_date_obj.year)
    month = f"{start_date_obj.month:02d}"
    filepath = os.path.join("data", "reports", "daily_report", year, month, filename)

    if not os.path.exists(filepath):
        return RedirectResponse(url="/reports/daily-balance", status_code=303)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )

@router.get("/reports/daily-balance/view/{year}/{month}/{filename}")
async def view_saved_daily_balance_report(
    request: Request,
    year: str,
    month: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    filepath = os.path.join("data", "reports", "daily_report", year, month, filename)
    print(f"\n\n=== VIEWING SAVED DAILY BALANCE REPORT ===", flush=True)
    print(f"Filepath: {filepath}", flush=True)
    print(f"File exists: {os.path.exists(filepath)}", flush=True)

    if not os.path.exists(filepath):
        return RedirectResponse(url="/reports/daily-balance", status_code=303)

    report_data = parse_daily_balance_csv(filepath)
    print(f"Report data keys: {report_data.keys() if report_data else 'None'}", flush=True)

    if not report_data:
        return RedirectResponse(url="/reports/daily-balance", status_code=303)

    return templates.TemplateResponse(
        "reports/view_saved_daily_balance_report.html",
        {
            "request": request,
            "current_user": current_user,
            "filename": filename,
            "report_data": report_data,
            "year": year,
            "month": month
        }
    )

@router.get("/reports/daily-balance/download/{year}/{month}/{filename}")
async def download_saved_daily_balance_report(
    year: str,
    month: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    filepath = os.path.join("data", "reports", "daily_report", year, month, filename)

    if not os.path.exists(filepath):
        return RedirectResponse(url="/reports/daily-balance", status_code=303)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )

@router.get("/reports/daily-balance/saved")
async def saved_daily_balance_reports(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    saved_reports = get_saved_daily_balance_reports()

    return templates.TemplateResponse(
        "reports/saved_daily_balance_reports.html",
        {
            "request": request,
            "current_user": current_user,
            "saved_reports": saved_reports
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
        employees_query = employees_query.filter(
            (Employee.name.ilike(f"%{search}%")) |
            (Employee.first_name.ilike(f"%{search}%")) |
            (Employee.last_name.ilike(f"%{search}%"))
        )

    employees = employees_query.order_by(Employee.last_name, Employee.first_name).all()

    for emp in employees:
        entry_count = db.query(DailyEmployeeEntry).filter(
            DailyEmployeeEntry.employee_id == emp.id
        ).join(DailyBalance).filter(
            DailyBalance.finalized == True
        ).count()
        emp.entry_count = entry_count

    saved_reports = get_saved_tip_reports(limit=4)

    return templates.TemplateResponse(
        "reports/tip_report_list.html",
        {
            "request": request,
            "current_user": current_user,
            "employees": employees,
            "search": search or "",
            "saved_reports": saved_reports
        }
    )

@router.get("/reports/tip-report/employee/{employee_slug}")
async def employee_tip_report(
    request: Request,
    employee_slug: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    month: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    employee = db.query(Employee).filter(Employee.slug == employee_slug).first()
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
        DailyEmployeeEntry.employee_id == employee.id
    ).join(DailyBalance).filter(
        DailyBalance.finalized == True,
        DailyBalance.date >= start_date_obj,
        DailyBalance.date <= end_date_obj
    ).order_by(DailyBalance.date.desc()).all()

    entries_by_position = {}
    all_tip_requirements = {}

    for entry in entries:
        if entry.position:
            pos_name = entry.position.name
            if pos_name not in entries_by_position:
                entries_by_position[pos_name] = {
                    "position": entry.position,
                    "entries": [],
                    "tip_totals": {}
                }
            entries_by_position[pos_name]["entries"].append(entry)

            if entry.position.tip_requirements:
                for req in entry.position.tip_requirements:
                    if req.field_name not in entries_by_position[pos_name]["tip_totals"]:
                        entries_by_position[pos_name]["tip_totals"][req.field_name] = 0
                    entries_by_position[pos_name]["tip_totals"][req.field_name] += entry.get_tip_value(req.field_name, 0)

                    if req.field_name not in all_tip_requirements:
                        all_tip_requirements[req.field_name] = req

    prev_month = target_date - relativedelta(months=1)
    next_month = target_date + relativedelta(months=1)

    return templates.TemplateResponse(
        "reports/employee_tip_detail.html",
        {
            "request": request,
            "current_user": current_user,
            "employee": employee,
            "entries": entries,
            "entries_by_position": entries_by_position,
            "start_date": start_date_obj,
            "end_date": end_date_obj,
            "current_month": target_date,
            "prev_month": prev_month,
            "next_month": next_month,
            "is_custom_range": bool(start_date and end_date)
        }
    )

@router.post("/reports/tip-report/employee/{employee_slug}/generate")
async def generate_employee_tip_report_endpoint(
    employee_slug: str,
    start_date: str = Form(...),
    end_date: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    employee = db.query(Employee).filter(Employee.slug == employee_slug).first()
    if not employee:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Employee not found"}
        )

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid date format"}
        )

    filename = generate_employee_tip_report_csv(db, employee, start_date_obj, end_date_obj, current_user=current_user, source="user")
    year = str(start_date_obj.year)
    month = f"{start_date_obj.month:02d}"
    filepath = os.path.join("data/reports/tip_report", year, month, filename)

    if not os.path.exists(filepath):
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Failed to generate report"}
        )

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Report generated successfully",
            "filename": filename
        }
    )

@router.get("/reports/tip-report/employee/{employee_slug}/export")
async def export_employee_tip_report(
    employee_slug: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    employee = db.query(Employee).filter(Employee.slug == employee_slug).first()
    if not employee:
        return RedirectResponse(url="/reports/tip-report", status_code=303)

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return RedirectResponse(url=f"/reports/tip-report/employee/{employee_slug}", status_code=303)

    filename = generate_employee_tip_report_csv(db, employee, start_date_obj, end_date_obj, current_user=current_user, source="user")
    year = str(start_date_obj.year)
    month = f"{start_date_obj.month:02d}"
    filepath = os.path.join("data/reports/tip_report", year, month, filename)

    if not os.path.exists(filepath):
        return RedirectResponse(url=f"/reports/tip-report/employee/{employee_slug}", status_code=303)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
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

    filename = generate_tip_report_csv(db, start_date_obj, end_date_obj, current_user=current_user, source="user")
    year = str(start_date_obj.year)
    month = f"{start_date_obj.month:02d}"
    filepath = os.path.join("data/reports/tip_report", year, month, filename)

    if not os.path.exists(filepath):
        return RedirectResponse(url="/reports/tip-report", status_code=303)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )

@router.get("/reports/tip-report/saved")
async def saved_tip_reports(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    saved_reports = get_saved_tip_reports()

    return templates.TemplateResponse(
        "reports/saved_tip_reports.html",
        {
            "request": request,
            "current_user": current_user,
            "saved_reports": saved_reports
        }
    )

@router.get("/reports/tip-report/view/{year}/{month}/{filename}")
async def view_saved_tip_report(
    request: Request,
    year: str,
    month: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    filepath = os.path.join("data/reports/tip_report", year, month, filename)

    if not os.path.exists(filepath):
        return RedirectResponse(url="/reports/tip-report", status_code=303)

    report_data = parse_tip_report_csv(filepath)

    if not report_data:
        return RedirectResponse(url="/reports/tip-report", status_code=303)

    print(f"DEBUG: Parsed report data - Summary count: {len(report_data.get('summary', []))}, Details count: {len(report_data.get('details', []))}")
    if report_data.get('summary'):
        print(f"DEBUG: First summary item: {report_data['summary'][0]}")

    return templates.TemplateResponse(
        "reports/view_saved_tip_report.html",
        {
            "request": request,
            "current_user": current_user,
            "filename": filename,
            "year": year,
            "month": month,
            "report_data": report_data
        }
    )

@router.get("/reports/tip-report/download/{year}/{month}/{filename}")
async def download_saved_tip_report(
    year: str,
    month: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    filepath = os.path.join("data/reports/tip_report", year, month, filename)

    if not os.path.exists(filepath):
        return RedirectResponse(url="/reports/tip-report", status_code=303)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )

@router.get("/reports/api/admin-users")
async def get_admin_users_for_email(
    report_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    admin_users = db.query(User).filter(
        User.is_admin == True,
        User.email.isnot(None),
        User.email != ""
    ).all()

    users_data = []
    for user in admin_users:
        opt_in = False
        if report_type == "daily" and user.opt_in_daily_reports:
            opt_in = True
        elif report_type == "tips" and user.opt_in_tip_reports:
            opt_in = True

        users_data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "opt_in": opt_in
        })

    return JSONResponse(
        status_code=200,
        content={"success": True, "users": users_data}
    )

@router.post("/reports/daily-balance/email")
async def email_daily_balance_report(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    form_data = await request.form()
    user_emails = form_data.getlist("user_emails[]")
    additional_email = form_data.get("additional_email", "").strip()
    attach_csv = form_data.get("attach_csv") == "on"

    email_list = []
    for email in user_emails:
        if email and validate_email(email):
            email_list.append(email)

    if additional_email and validate_email(additional_email):
        email_list.append(additional_email)

    if not email_list:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No valid email addresses provided"}
        )

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid date format"}
        )

    year = str(start_date_obj.year)
    month = f"{start_date_obj.month:02d}"

    if start_date_obj == end_date_obj:
        filename = f"{start_date_obj}-daily-balance.csv"
        filepath = os.path.join("data", "reports", "daily_report", year, month, filename)

        if not os.path.exists(filepath):
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Report file not found"}
            )

        date_display = start_date_obj.strftime('%B %d, %Y')
        subject = f"Daily Balance Report - {date_display}"
    else:
        filename = generate_consolidated_daily_balance_csv(db, start_date_obj, end_date_obj, current_user=current_user, source="user")
        filepath = os.path.join("data", "reports", "daily_report", year, month, filename)

        if not os.path.exists(filepath):
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Report file not found"}
            )

        date_display = f"{start_date_obj.strftime('%B %d, %Y')} to {end_date_obj.strftime('%B %d, %Y')}"
        subject = f"Daily Balance Report - {date_display}"

    result = send_report_emails(
        to_emails=email_list,
        report_type="daily",
        report_filepath=filepath,
        subject=subject,
        date_range=date_display,
        attach_csv=attach_csv
    )

    if result["success"]:
        return JSONResponse(
            status_code=200,
            content=result
        )
    else:
        return JSONResponse(
            status_code=500,
            content=result
        )

@router.post("/reports/daily-balance/email/{year}/{month}/{filename}")
async def email_saved_daily_balance_report(
    request: Request,
    year: str,
    month: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    form_data = await request.form()
    user_emails = form_data.getlist("user_emails[]")
    additional_email = form_data.get("additional_email", "").strip()
    attach_csv = form_data.get("attach_csv") == "on"

    email_list = []
    for email in user_emails:
        if email and validate_email(email):
            email_list.append(email)

    if additional_email and validate_email(additional_email):
        email_list.append(additional_email)

    if not email_list:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No valid email addresses provided"}
        )

    filepath = os.path.join("data", "reports", "daily_report", year, month, filename)

    if not os.path.exists(filepath):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Report file not found"}
        )

    subject = f"Daily Balance Report - {filename}"

    result = send_report_emails(
        to_emails=email_list,
        report_type="daily",
        report_filepath=filepath,
        subject=subject,
        attach_csv=attach_csv
    )

    if result["success"]:
        return JSONResponse(
            status_code=200,
            content=result
        )
    else:
        return JSONResponse(
            status_code=500,
            content=result
        )

@router.post("/reports/tip-report/email")
async def email_tip_report(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    form_data = await request.form()
    user_emails = form_data.getlist("user_emails[]")
    additional_email = form_data.get("additional_email", "").strip()
    attach_csv = form_data.get("attach_csv") == "on"

    email_list = []
    for email in user_emails:
        if email and validate_email(email):
            email_list.append(email)

    if additional_email and validate_email(additional_email):
        email_list.append(additional_email)

    if not email_list:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No valid email addresses provided"}
        )

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid date format"}
        )

    filename = generate_tip_report_csv(db, start_date_obj, end_date_obj, current_user=current_user, source="user")
    year = str(start_date_obj.year)
    month = f"{start_date_obj.month:02d}"
    filepath = os.path.join("data/reports/tip_report", year, month, filename)

    if not os.path.exists(filepath):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Report file not found"}
        )

    date_range = f"{start_date_obj.strftime('%B %d, %Y')} to {end_date_obj.strftime('%B %d, %Y')}"
    subject = f"Tip Report - {date_range}"

    result = send_report_emails(
        to_emails=email_list,
        report_type="tips",
        report_filepath=filepath,
        subject=subject,
        date_range=date_range,
        attach_csv=attach_csv
    )

    if result["success"]:
        return JSONResponse(
            status_code=200,
            content=result
        )
    else:
        return JSONResponse(
            status_code=500,
            content=result
        )

@router.post("/reports/tip-report/email/{year}/{month}/{filename}")
async def email_saved_tip_report(
    request: Request,
    year: str,
    month: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    form_data = await request.form()
    user_emails = form_data.getlist("user_emails[]")
    additional_email = form_data.get("additional_email", "").strip()
    attach_csv = form_data.get("attach_csv") == "on"

    email_list = []
    for email in user_emails:
        if email and validate_email(email):
            email_list.append(email)

    if additional_email and validate_email(additional_email):
        email_list.append(additional_email)

    if not email_list:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No valid email addresses provided"}
        )

    filepath = os.path.join("data/reports/tip_report", year, month, filename)

    if not os.path.exists(filepath):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Report file not found"}
        )

    subject = f"Tip Report - {filename}"

    result = send_report_emails(
        to_emails=email_list,
        report_type="tips",
        report_filepath=filepath,
        subject=subject,
        attach_csv=attach_csv
    )

    if result["success"]:
        return JSONResponse(
            status_code=200,
            content=result
        )
    else:
        return JSONResponse(
            status_code=500,
            content=result
        )

@router.post("/reports/tip-report/employee/{employee_slug}/email")
async def email_employee_tip_report(
    request: Request,
    employee_slug: str,
    start_date: str = Form(...),
    end_date: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Unauthorized"}
        )

    employee = db.query(Employee).filter(Employee.slug == employee_slug).first()
    if not employee:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Employee not found"}
        )

    form_data = await request.form()
    user_emails = form_data.getlist("user_emails[]")
    additional_email = form_data.get("additional_email", "").strip()
    attach_csv = form_data.get("attach_csv") == "on"

    email_list = []
    for email in user_emails:
        if email and validate_email(email):
            email_list.append(email)

    if additional_email and validate_email(additional_email):
        email_list.append(additional_email)

    if not email_list:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No valid email addresses provided"}
        )

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid date format"}
        )

    filename = generate_employee_tip_report_csv(db, employee, start_date_obj, end_date_obj)
    year = str(start_date_obj.year)
    month = f"{start_date_obj.month:02d}"
    filepath = os.path.join("data/reports/tip_report", year, month, filename)

    if not os.path.exists(filepath):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Report file not found"}
        )

    date_range = f"{start_date_obj.strftime('%B %d, %Y')} to {end_date_obj.strftime('%B %d, %Y')}"
    subject = f"Tip Report for {employee.display_name} - {date_range}"

    result = send_report_emails(
        to_emails=email_list,
        report_type="tips",
        report_filepath=filepath,
        subject=subject,
        date_range=date_range,
        attach_csv=attach_csv
    )

    if result["success"]:
        return JSONResponse(
            status_code=200,
            content=result
        )
    else:
        return JSONResponse(
            status_code=500,
            content=result
        )
