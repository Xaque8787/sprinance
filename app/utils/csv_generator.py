import csv
import os
from datetime import date, datetime
from typing import List
from sqlalchemy.orm import Session
from app.models import DailyBalance, DailyEmployeeEntry, Employee

def generate_daily_balance_csv(daily_balance: DailyBalance, employee_entries: List[DailyEmployeeEntry]) -> str:
    # Sort employees by last name, first name
    employee_entries = sorted(employee_entries, key=lambda e: (e.employee.last_name or '', e.employee.first_name or ''))

    # Parse the date to get year and month
    if isinstance(daily_balance.date, str):
        date_obj = datetime.strptime(daily_balance.date, '%Y-%m-%d').date()
    else:
        date_obj = daily_balance.date

    year = str(date_obj.year)
    month = f"{date_obj.month:02d}"

    # Create the directory structure: data/reports/daily_report/{year}/{month}/
    reports_dir = os.path.join("data", "reports", "daily_report", year, month)
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    filename = f"{daily_balance.date}-daily-balance.csv"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["Daily Balance Report"])
        writer.writerow(["Date Range", str(daily_balance.date)])
        writer.writerow([])

        writer.writerow([f"Date: {daily_balance.date} - {daily_balance.day_of_week}"])
        if daily_balance.notes:
            writer.writerow(["Notes", daily_balance.notes])
        writer.writerow([])

        writer.writerow(["Revenue & Income"])
        revenue_items = [item for item in daily_balance.financial_line_items if item.category == "revenue"]
        revenue_total = 0
        for item in sorted(revenue_items, key=lambda x: x.display_order):
            writer.writerow([item.name, f"${item.value:.2f}"])
            revenue_total += item.value
        writer.writerow(["Total Revenue", f"${revenue_total:.2f}"])
        writer.writerow([])

        writer.writerow(["Deposits & Expenses"])
        expense_items = [item for item in daily_balance.financial_line_items if item.category == "expense"]
        expense_total = 0
        for item in sorted(expense_items, key=lambda x: x.display_order):
            writer.writerow([item.name, f"${item.value:.2f}"])
            expense_total += item.value
        writer.writerow(["Total Expenses", f"${expense_total:.2f}"])
        writer.writerow([])

        cash_over_under = expense_total - revenue_total
        writer.writerow(["Cash Over/Under", f"${cash_over_under:.2f}"])
        writer.writerow([])

        writer.writerow(["Employee Breakdown"])
        writer.writerow([
            "Employee Name",
            "Position",
            "Bank Card Sales",
            "Bank Card Tips",
            "Cash Tips",
            "Total Sales",
            "Adjustments",
            "Tips on Paycheck",
            "Tip Out",
            "Take-Home Tips"
        ])

        for entry in employee_entries:
            writer.writerow([
                entry.employee.display_name,
                entry.employee.position.name,
                f"${entry.bank_card_sales:.2f}",
                f"${entry.bank_card_tips:.2f}",
                f"${entry.cash_tips:.2f}",
                f"${entry.total_sales:.2f}",
                f"${entry.adjustments:.2f}",
                f"${entry.tips_on_paycheck:.2f}",
                f"${entry.tip_out:.2f}",
                f"${entry.calculated_take_home:.2f}"
            ])

    return filepath

def generate_tip_report_csv(db: Session, start_date: date, end_date: date) -> str:
    reports_dir = "data/reports/tip_report"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    filename = f"tip-report-{start_date}-to-{end_date}.csv"
    filepath = os.path.join(reports_dir, filename)

    employees = db.query(Employee).order_by(Employee.last_name, Employee.first_name).all()

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["Employee Tip Report"])
        writer.writerow(["Date Range", f"{start_date} to {end_date}"])
        writer.writerow([])

        # Payroll Summary Section
        writer.writerow(["PAYROLL SUMMARY"])
        writer.writerow([])

        payroll_summary_data = []
        payroll_reqs_map = {}  # Maps field_name to requirement name

        for employee in employees:
            entries = db.query(DailyEmployeeEntry).filter(
                DailyEmployeeEntry.employee_id == employee.id
            ).join(DailyBalance).filter(
                DailyBalance.finalized == True,
                DailyBalance.date >= start_date,
                DailyBalance.date <= end_date
            ).all()

            if entries and employee.position.tip_requirements:
                payroll_reqs = [req for req in employee.position.tip_requirements if req.include_in_payroll_summary]

                if payroll_reqs:
                    emp_data = {"employee": employee.display_name, "position": employee.position.name}

                    for req in payroll_reqs:
                        if req.field_name not in payroll_reqs_map:
                            payroll_reqs_map[req.field_name] = req.name

                        total = 0
                        for entry in entries:
                            if entry.tip_values:
                                total += entry.tip_values.get(req.field_name, 0)
                        emp_data[req.field_name] = total

                    payroll_summary_data.append(emp_data)

        if payroll_summary_data:
            header_row = ["Employee Name", "Position"] + [payroll_reqs_map[field] for field in payroll_reqs_map.keys()]
            writer.writerow(header_row)

            for emp_data in payroll_summary_data:
                row = [emp_data["employee"], emp_data["position"]]
                for field in payroll_reqs_map.keys():
                    value = emp_data.get(field, 0)
                    row.append(f"${value:.2f}")
                writer.writerow(row)
        else:
            writer.writerow(["No payroll summary data available for this period"])

        writer.writerow([])
        writer.writerow([])

        # Regular Summary Section
        writer.writerow(["EMPLOYEE SUMMARY"])
        writer.writerow([])
        writer.writerow([
            "Employee Name",
            "Position",
            "Total Bank Card Tips",
            "Total Cash Tips",
            "Total Adjustments",
            "Total Tips on Paycheck",
            "Total Tip Out",
            "Total Take Home",
            "Number of Shifts"
        ])

        for employee in employees:
            entries = db.query(DailyEmployeeEntry).filter(
                DailyEmployeeEntry.employee_id == employee.id
            ).join(DailyBalance).filter(
                DailyBalance.finalized == True,
                DailyBalance.date >= start_date,
                DailyBalance.date <= end_date
            ).all()

            if entries:
                total_bank_card_tips = sum(entry.bank_card_tips or 0 for entry in entries)
                total_cash_tips = sum(entry.cash_tips or 0 for entry in entries)
                total_adjustments = sum(entry.adjustments or 0 for entry in entries)
                total_tips_on_paycheck = sum(entry.tips_on_paycheck or 0 for entry in entries)
                total_tip_out = sum(entry.tip_out or 0 for entry in entries)
                total_take_home = sum(entry.calculated_take_home or 0 for entry in entries)
                num_shifts = len(entries)

                writer.writerow([
                    employee.display_name,
                    employee.position.name,
                    f"${total_bank_card_tips:.2f}",
                    f"${total_cash_tips:.2f}",
                    f"${total_adjustments:.2f}",
                    f"${total_tips_on_paycheck:.2f}",
                    f"${total_tip_out:.2f}",
                    f"${total_take_home:.2f}",
                    num_shifts
                ])

        writer.writerow([])
        writer.writerow(["Detailed Daily Breakdown by Employee"])
        writer.writerow([])

        for employee in employees:
            entries = db.query(DailyEmployeeEntry).filter(
                DailyEmployeeEntry.employee_id == employee.id
            ).join(DailyBalance).filter(
                DailyBalance.finalized == True,
                DailyBalance.date >= start_date,
                DailyBalance.date <= end_date
            ).order_by(DailyBalance.date).all()

            if entries:
                writer.writerow([f"Employee: {employee.display_name} - {employee.position.name}"])
                writer.writerow([
                    "Date",
                    "Day",
                    "Bank Card Sales",
                    "Bank Card Tips",
                    "Total Sales",
                    "Cash Tips",
                    "Adjustments",
                    "Tips on Paycheck",
                    "Tip Out",
                    "Take Home"
                ])

                for entry in entries:
                    writer.writerow([
                        entry.daily_balance.date,
                        entry.daily_balance.day_of_week,
                        f"${entry.bank_card_sales:.2f}",
                        f"${entry.bank_card_tips:.2f}",
                        f"${entry.total_sales:.2f}",
                        f"${entry.cash_tips:.2f}",
                        f"${entry.adjustments:.2f}",
                        f"${entry.tips_on_paycheck:.2f}",
                        f"${entry.tip_out:.2f}",
                        f"${entry.calculated_take_home:.2f}"
                    ])

                total_bank_card_tips = sum(entry.bank_card_tips or 0 for entry in entries)
                total_cash_tips = sum(entry.cash_tips or 0 for entry in entries)
                total_adjustments = sum(entry.adjustments or 0 for entry in entries)
                total_tips_on_paycheck = sum(entry.tips_on_paycheck or 0 for entry in entries)
                total_take_home = sum(entry.calculated_take_home or 0 for entry in entries)

                writer.writerow([
                    "TOTAL",
                    "",
                    "",
                    f"${total_bank_card_tips:.2f}",
                    "",
                    f"${total_cash_tips:.2f}",
                    f"${total_adjustments:.2f}",
                    f"${total_tips_on_paycheck:.2f}",
                    f"${total_take_home:.2f}"
                ])
                writer.writerow([])

    return filename

def generate_consolidated_daily_balance_csv(db: Session, start_date: date, end_date: date) -> str:
    year = str(start_date.year)
    month = f"{start_date.month:02d}"

    reports_dir = os.path.join("data", "reports", "daily_report", year, month)
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    filename = f"daily-balance-{start_date}-to-{end_date}.csv"
    filepath = os.path.join(reports_dir, filename)

    daily_balances = db.query(DailyBalance).filter(
        DailyBalance.finalized == True,
        DailyBalance.date >= start_date,
        DailyBalance.date <= end_date
    ).order_by(DailyBalance.date).all()

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["Consolidated Daily Balance Report"])
        writer.writerow(["Date Range", f"{start_date} to {end_date}"])
        writer.writerow([])

        if not daily_balances:
            writer.writerow(["No finalized reports found for this date range"])
            return filename

        for daily_balance in daily_balances:
            writer.writerow([f"Date: {daily_balance.date} - {daily_balance.day_of_week}"])
            if daily_balance.notes:
                writer.writerow(["Notes", daily_balance.notes])
            writer.writerow([])

            writer.writerow(["Revenue & Income"])
            revenue_items = [item for item in daily_balance.financial_line_items if item.category == "revenue"]
            revenue_total = 0
            for item in sorted(revenue_items, key=lambda x: x.display_order):
                writer.writerow([item.name, f"${item.value:.2f}"])
                revenue_total += item.value
            writer.writerow(["Total Revenue", f"${revenue_total:.2f}"])
            writer.writerow([])

            writer.writerow(["Deposits & Expenses"])
            expense_items = [item for item in daily_balance.financial_line_items if item.category == "expense"]
            expense_total = 0
            for item in sorted(expense_items, key=lambda x: x.display_order):
                writer.writerow([item.name, f"${item.value:.2f}"])
                expense_total += item.value
            writer.writerow(["Total Expenses", f"${expense_total:.2f}"])
            writer.writerow([])

            cash_over_under = expense_total - revenue_total
            writer.writerow(["Cash Over/Under", f"${cash_over_under:.2f}"])
            writer.writerow([])

            writer.writerow(["Employee Breakdown"])
            writer.writerow([
                "Employee Name",
                "Position",
                "Bank Card Sales",
                "Bank Card Tips",
                "Cash Tips",
                "Total Sales",
                "Adjustments",
                "Tips on Paycheck",
                "Tip Out",
                "Take-Home Tips"
            ])

            sorted_entries = sorted(daily_balance.employee_entries, key=lambda e: (e.employee.last_name or '', e.employee.first_name or ''))
            for entry in sorted_entries:
                writer.writerow([
                    entry.employee.display_name,
                    entry.employee.position.name,
                    f"${entry.bank_card_sales:.2f}",
                    f"${entry.bank_card_tips:.2f}",
                    f"${entry.cash_tips:.2f}",
                    f"${entry.total_sales:.2f}",
                    f"${entry.adjustments:.2f}",
                    f"${entry.tips_on_paycheck:.2f}",
                    f"${entry.tip_out:.2f}",
                    f"${entry.calculated_take_home:.2f}"
                ])

            writer.writerow([])
            writer.writerow(["=" * 80])
            writer.writerow([])

        writer.writerow(["Summary Totals for Period"])
        writer.writerow([])

        total_revenue = 0
        total_expenses = 0

        for daily_balance in daily_balances:
            revenue_items = [item for item in daily_balance.financial_line_items if item.category == "revenue"]
            total_revenue += sum(item.value for item in revenue_items)

            expense_items = [item for item in daily_balance.financial_line_items if item.category == "expense"]
            total_expenses += sum(item.value for item in expense_items)

        writer.writerow(["Total Revenue for Period", f"${total_revenue:.2f}"])
        writer.writerow(["Total Expenses for Period", f"${total_expenses:.2f}"])
        writer.writerow(["Net Cash Over/Under", f"${total_expenses - total_revenue:.2f}"])

    return filename

def generate_employee_tip_report_csv(db: Session, employee: Employee, start_date: date, end_date: date) -> str:
    reports_dir = "data/reports/tip_report"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    employee_slug = employee.slug
    filename = f"tip-report-{employee_slug}-{start_date}-to-{end_date}.csv"
    filepath = os.path.join(reports_dir, filename)

    entries = db.query(DailyEmployeeEntry).filter(
        DailyEmployeeEntry.employee_id == employee.id
    ).join(DailyBalance).filter(
        DailyBalance.finalized == True,
        DailyBalance.date >= start_date,
        DailyBalance.date <= end_date
    ).order_by(DailyBalance.date).all()

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["Employee Tip Report"])
        writer.writerow(["Employee", employee.display_name])
        writer.writerow(["Position", employee.position.name])
        writer.writerow(["Date Range", f"{start_date} to {end_date}"])
        writer.writerow([])

        if not entries:
            writer.writerow(["No entries found for this employee in the selected date range"])
            return filename

        # Payroll Summary Section
        if employee.position.tip_requirements:
            payroll_reqs = [req for req in employee.position.tip_requirements if req.include_in_payroll_summary]

            if payroll_reqs:
                writer.writerow(["PAYROLL SUMMARY"])
                writer.writerow([])

                for req in payroll_reqs:
                    total = 0
                    for entry in entries:
                        if entry.tip_values:
                            total += entry.tip_values.get(req.field_name, 0)
                    writer.writerow([req.name, f"${total:.2f}"])

                writer.writerow([])
                writer.writerow([])

        total_bank_card_tips = sum(entry.bank_card_tips or 0 for entry in entries)
        total_cash_tips = sum(entry.cash_tips or 0 for entry in entries)
        total_adjustments = sum(entry.adjustments or 0 for entry in entries)
        total_tips_on_paycheck = sum(entry.tips_on_paycheck or 0 for entry in entries)
        total_tip_out = sum(entry.tip_out or 0 for entry in entries)
        total_take_home = sum(entry.calculated_take_home or 0 for entry in entries)
        num_shifts = len(entries)

        writer.writerow(["Summary"])
        writer.writerow(["Total Bank Card Tips", f"${total_bank_card_tips:.2f}"])
        writer.writerow(["Total Cash Tips", f"${total_cash_tips:.2f}"])
        writer.writerow(["Total Adjustments", f"${total_adjustments:.2f}"])
        writer.writerow(["Total Tips on Paycheck", f"${total_tips_on_paycheck:.2f}"])
        writer.writerow(["Total Tip Out", f"${total_tip_out:.2f}"])
        writer.writerow(["Total Take Home", f"${total_take_home:.2f}"])
        writer.writerow(["Number of Shifts", num_shifts])
        writer.writerow([])

        writer.writerow(["Daily Breakdown"])
        writer.writerow([
            "Date",
            "Day",
            "Bank Card Sales",
            "Bank Card Tips",
            "Total Sales",
            "Cash Tips",
            "Adjustments",
            "Tips on Paycheck",
            "Tip Out",
            "Take Home"
        ])

        for entry in entries:
            writer.writerow([
                entry.daily_balance.date,
                entry.daily_balance.day_of_week,
                f"${entry.bank_card_sales:.2f}",
                f"${entry.bank_card_tips:.2f}",
                f"${entry.total_sales:.2f}",
                f"${entry.cash_tips:.2f}",
                f"${entry.adjustments:.2f}",
                f"${entry.tips_on_paycheck:.2f}",
                f"${entry.tip_out:.2f}",
                f"${entry.calculated_take_home:.2f}"
            ])

        writer.writerow([])
        writer.writerow([
            "TOTAL",
            "",
            "",
            f"${total_bank_card_tips:.2f}",
            "",
            f"${total_cash_tips:.2f}",
            f"${total_adjustments:.2f}",
            f"${total_tips_on_paycheck:.2f}",
            f"${total_tip_out:.2f}",
            f"${total_take_home:.2f}"
        ])

    return filename
