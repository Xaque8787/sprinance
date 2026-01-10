from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date as date_cls, datetime
from typing import List, Optional
import os
from app.database import get_db
from app.models import User, Employee, DailyBalance, DailyEmployeeEntry
from app.auth.jwt_handler import get_current_user
from app.utils.csv_generator import generate_daily_balance_csv

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

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
            "edit_mode": edit
        }
    )

@router.post("/daily-balance/save")
async def save_daily_balance(
    request: Request,
    target_date: str = Form(...),
    notes: str = Form(""),
    cash_drawers_beginning: float = Form(0.0),
    food_sales: float = Form(0.0),
    non_alcohol_beverage_sales: float = Form(0.0),
    beer_sales: float = Form(0.0),
    wine_sales: float = Form(0.0),
    other_revenue: float = Form(0.0),
    catering_sales: float = Form(0.0),
    fundraising_contributions: float = Form(0.0),
    sales_tax_payable: float = Form(0.0),
    gift_certificate_sold: float = Form(0.0),
    gift_certificate_redeemed: float = Form(0.0),
    checking_account_cash_deposit: float = Form(0.0),
    checking_account_bank_cards: float = Form(0.0),
    cash_paid_out: float = Form(0.0),
    cash_drawers_end: float = Form(0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    day_of_week = DAYS_OF_WEEK[date_obj.weekday()]

    daily_balance = db.query(DailyBalance).filter(DailyBalance.date == date_obj).first()

    if not daily_balance:
        daily_balance = DailyBalance(
            date=date_obj,
            day_of_week=day_of_week,
            notes=notes,
            finalized=False,
            cash_drawers_beginning=cash_drawers_beginning,
            food_sales=food_sales,
            non_alcohol_beverage_sales=non_alcohol_beverage_sales,
            beer_sales=beer_sales,
            wine_sales=wine_sales,
            other_revenue=other_revenue,
            catering_sales=catering_sales,
            fundraising_contributions=fundraising_contributions,
            sales_tax_payable=sales_tax_payable,
            gift_certificate_sold=gift_certificate_sold,
            gift_certificate_redeemed=gift_certificate_redeemed,
            checking_account_cash_deposit=checking_account_cash_deposit,
            checking_account_bank_cards=checking_account_bank_cards,
            cash_paid_out=cash_paid_out,
            cash_drawers_end=cash_drawers_end
        )
        db.add(daily_balance)
        db.flush()
    else:
        daily_balance.notes = notes
        daily_balance.cash_drawers_beginning = cash_drawers_beginning
        daily_balance.food_sales = food_sales
        daily_balance.non_alcohol_beverage_sales = non_alcohol_beverage_sales
        daily_balance.beer_sales = beer_sales
        daily_balance.wine_sales = wine_sales
        daily_balance.other_revenue = other_revenue
        daily_balance.catering_sales = catering_sales
        daily_balance.fundraising_contributions = fundraising_contributions
        daily_balance.sales_tax_payable = sales_tax_payable
        daily_balance.gift_certificate_sold = gift_certificate_sold
        daily_balance.gift_certificate_redeemed = gift_certificate_redeemed
        daily_balance.checking_account_cash_deposit = checking_account_cash_deposit
        daily_balance.checking_account_bank_cards = checking_account_bank_cards
        daily_balance.cash_paid_out = cash_paid_out
        daily_balance.cash_drawers_end = cash_drawers_end

    form_data = await request.form()

    employee_ids = form_data.getlist("employee_ids")
    employee_ids = [int(emp_id) for emp_id in employee_ids if emp_id]

    for entry in daily_balance.employee_entries:
        db.delete(entry)
    db.flush()

    for emp_id in employee_ids:
        bank_card_sales = float(form_data.get(f"bank_card_sales_{emp_id}", 0.0))
        bank_card_tips = float(form_data.get(f"bank_card_tips_{emp_id}", 0.0))
        cash_tips = float(form_data.get(f"cash_tips_{emp_id}", 0.0))
        total_sales = float(form_data.get(f"total_sales_{emp_id}", 0.0))
        adjustments = float(form_data.get(f"adjustments_{emp_id}", 0.0))

        calculated_take_home = bank_card_tips + cash_tips + adjustments

        entry = DailyEmployeeEntry(
            daily_balance_id=daily_balance.id,
            employee_id=emp_id,
            bank_card_sales=bank_card_sales,
            bank_card_tips=bank_card_tips,
            cash_tips=cash_tips,
            total_sales=total_sales,
            adjustments=adjustments,
            calculated_take_home=calculated_take_home
        )
        db.add(entry)

    db.commit()

    return RedirectResponse(url=f"/daily-balance?selected_date={target_date}", status_code=302)

@router.post("/daily-balance/finalize")
async def finalize_daily_balance(
    request: Request,
    target_date: str = Form(...),
    notes: str = Form(""),
    cash_drawers_beginning: float = Form(0.0),
    food_sales: float = Form(0.0),
    non_alcohol_beverage_sales: float = Form(0.0),
    beer_sales: float = Form(0.0),
    wine_sales: float = Form(0.0),
    other_revenue: float = Form(0.0),
    catering_sales: float = Form(0.0),
    fundraising_contributions: float = Form(0.0),
    sales_tax_payable: float = Form(0.0),
    gift_certificate_sold: float = Form(0.0),
    gift_certificate_redeemed: float = Form(0.0),
    checking_account_cash_deposit: float = Form(0.0),
    checking_account_bank_cards: float = Form(0.0),
    cash_paid_out: float = Form(0.0),
    cash_drawers_end: float = Form(0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    day_of_week = DAYS_OF_WEEK[date_obj.weekday()]

    daily_balance = db.query(DailyBalance).filter(DailyBalance.date == date_obj).first()

    if not daily_balance:
        daily_balance = DailyBalance(
            date=date_obj,
            day_of_week=day_of_week,
            notes=notes,
            finalized=True,
            cash_drawers_beginning=cash_drawers_beginning,
            food_sales=food_sales,
            non_alcohol_beverage_sales=non_alcohol_beverage_sales,
            beer_sales=beer_sales,
            wine_sales=wine_sales,
            other_revenue=other_revenue,
            catering_sales=catering_sales,
            fundraising_contributions=fundraising_contributions,
            sales_tax_payable=sales_tax_payable,
            gift_certificate_sold=gift_certificate_sold,
            gift_certificate_redeemed=gift_certificate_redeemed,
            checking_account_cash_deposit=checking_account_cash_deposit,
            checking_account_bank_cards=checking_account_bank_cards,
            cash_paid_out=cash_paid_out,
            cash_drawers_end=cash_drawers_end
        )
        db.add(daily_balance)
        db.flush()
    else:
        daily_balance.notes = notes
        daily_balance.finalized = True
        daily_balance.cash_drawers_beginning = cash_drawers_beginning
        daily_balance.food_sales = food_sales
        daily_balance.non_alcohol_beverage_sales = non_alcohol_beverage_sales
        daily_balance.beer_sales = beer_sales
        daily_balance.wine_sales = wine_sales
        daily_balance.other_revenue = other_revenue
        daily_balance.catering_sales = catering_sales
        daily_balance.fundraising_contributions = fundraising_contributions
        daily_balance.sales_tax_payable = sales_tax_payable
        daily_balance.gift_certificate_sold = gift_certificate_sold
        daily_balance.gift_certificate_redeemed = gift_certificate_redeemed
        daily_balance.checking_account_cash_deposit = checking_account_cash_deposit
        daily_balance.checking_account_bank_cards = checking_account_bank_cards
        daily_balance.cash_paid_out = cash_paid_out
        daily_balance.cash_drawers_end = cash_drawers_end

    form_data = await request.form()

    employee_ids = form_data.getlist("employee_ids")
    employee_ids = [int(emp_id) for emp_id in employee_ids if emp_id]

    for entry in daily_balance.employee_entries:
        db.delete(entry)
    db.flush()

    for emp_id in employee_ids:
        bank_card_sales = float(form_data.get(f"bank_card_sales_{emp_id}", 0.0))
        bank_card_tips = float(form_data.get(f"bank_card_tips_{emp_id}", 0.0))
        cash_tips = float(form_data.get(f"cash_tips_{emp_id}", 0.0))
        total_sales = float(form_data.get(f"total_sales_{emp_id}", 0.0))
        adjustments = float(form_data.get(f"adjustments_{emp_id}", 0.0))

        calculated_take_home = bank_card_tips + cash_tips + adjustments

        entry = DailyEmployeeEntry(
            daily_balance_id=daily_balance.id,
            employee_id=emp_id,
            bank_card_sales=bank_card_sales,
            bank_card_tips=bank_card_tips,
            cash_tips=cash_tips,
            total_sales=total_sales,
            adjustments=adjustments,
            calculated_take_home=calculated_take_home
        )
        db.add(entry)

    db.commit()
    db.refresh(daily_balance)

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
