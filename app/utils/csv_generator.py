import csv
import os
from datetime import date
from typing import List
from sqlalchemy.orm import Session
from app.models import DailyBalance, DailyEmployeeEntry, Employee

def generate_daily_balance_csv(daily_balance: DailyBalance, employee_entries: List[DailyEmployeeEntry]) -> str:
    reports_dir = "data/reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    filename = f"{daily_balance.date}-daily-balance.csv"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["Daily Balance Report"])
        writer.writerow(["Date", daily_balance.date])
        writer.writerow(["Day of Week", daily_balance.day_of_week])
        if daily_balance.notes:
            writer.writerow(["Notes", daily_balance.notes])
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
            "Take-Home Tips"
        ])

        for entry in employee_entries:
            writer.writerow([
                entry.employee.name,
                entry.employee.position.name,
                f"${entry.bank_card_sales:.2f}",
                f"${entry.bank_card_tips:.2f}",
                f"${entry.cash_tips:.2f}",
                f"${entry.total_sales:.2f}",
                f"${entry.adjustments:.2f}",
                f"${entry.calculated_take_home:.2f}"
            ])

    return filepath

def generate_tip_report_csv(db: Session, start_date: date, end_date: date) -> str:
    reports_dir = "data/reports/tip_report"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    filename = f"tip-report-{start_date}-to-{end_date}.csv"
    filepath = os.path.join(reports_dir, filename)

    employees = db.query(Employee).order_by(Employee.name).all()

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["Employee Tip Report"])
        writer.writerow(["Date Range", f"{start_date} to {end_date}"])
        writer.writerow([])

        writer.writerow([
            "Employee Name",
            "Position",
            "Total Bank Card Tips",
            "Total Cash Tips",
            "Total Adjustments",
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
                total_take_home = sum(entry.calculated_take_home or 0 for entry in entries)
                num_shifts = len(entries)

                writer.writerow([
                    employee.name,
                    employee.position.name,
                    f"${total_bank_card_tips:.2f}",
                    f"${total_cash_tips:.2f}",
                    f"${total_adjustments:.2f}",
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
                writer.writerow([f"Employee: {employee.name} - {employee.position.name}"])
                writer.writerow([
                    "Date",
                    "Day",
                    "Bank Card Sales",
                    "Bank Card Tips",
                    "Total Sales",
                    "Cash Tips",
                    "Adjustments",
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
                        f"${entry.calculated_take_home:.2f}"
                    ])

                total_bank_card_tips = sum(entry.bank_card_tips or 0 for entry in entries)
                total_cash_tips = sum(entry.cash_tips or 0 for entry in entries)
                total_adjustments = sum(entry.adjustments or 0 for entry in entries)
                total_take_home = sum(entry.calculated_take_home or 0 for entry in entries)

                writer.writerow([
                    "TOTAL",
                    "",
                    "",
                    f"${total_bank_card_tips:.2f}",
                    "",
                    f"${total_cash_tips:.2f}",
                    f"${total_adjustments:.2f}",
                    f"${total_take_home:.2f}"
                ])
                writer.writerow([])

    return filename
