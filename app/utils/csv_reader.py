import csv
import os
from datetime import datetime
from typing import List, Dict, Any

def get_saved_daily_balance_reports(limit: int = None) -> List[Dict[str, Any]]:
    reports_base_dir = "data/reports/daily_report"
    if not os.path.exists(reports_base_dir):
        return []

    reports = []
    for year_dir in os.listdir(reports_base_dir):
        year_path = os.path.join(reports_base_dir, year_dir)
        if not os.path.isdir(year_path):
            continue

        for month_dir in os.listdir(year_path):
            month_path = os.path.join(year_path, month_dir)
            if not os.path.isdir(month_path):
                continue

            for filename in os.listdir(month_path):
                if filename.endswith('.csv') and 'daily-balance-' in filename:
                    filepath = os.path.join(month_path, filename)
                    file_stats = os.stat(filepath)
                    created_time = datetime.fromtimestamp(file_stats.st_mtime)

                    start_date = None
                    end_date = None
                    if filename.startswith('daily-balance-') and filename.endswith('.csv'):
                        parts = filename.replace('daily-balance-', '').replace('.csv', '').split('-to-')
                        if len(parts) == 2:
                            try:
                                start_date = datetime.strptime(parts[0], '%Y-%m-%d').date()
                                end_date = datetime.strptime(parts[1], '%Y-%m-%d').date()
                            except ValueError:
                                pass

                    reports.append({
                        'filename': filename,
                        'filepath': filepath,
                        'created_time': created_time,
                        'start_date': start_date,
                        'end_date': end_date,
                        'file_size': file_stats.st_size,
                        'year': year_dir,
                        'month': month_dir
                    })

    reports.sort(key=lambda x: x['created_time'], reverse=True)

    if limit:
        reports = reports[:limit]

    return reports

def get_saved_tip_reports(limit: int = None) -> List[Dict[str, Any]]:
    reports_dir = "data/reports/tip_report"
    if not os.path.exists(reports_dir):
        return []

    reports = []
    for filename in os.listdir(reports_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(reports_dir, filename)
            file_stats = os.stat(filepath)
            created_time = datetime.fromtimestamp(file_stats.st_mtime)

            start_date = None
            end_date = None
            if filename.startswith('tip-report-') and filename.endswith('.csv'):
                parts = filename.replace('tip-report-', '').replace('.csv', '').split('-to-')
                if len(parts) == 2:
                    try:
                        start_date = datetime.strptime(parts[0], '%Y-%m-%d').date()
                        end_date = datetime.strptime(parts[1], '%Y-%m-%d').date()
                    except ValueError:
                        pass

            reports.append({
                'filename': filename,
                'filepath': filepath,
                'created_time': created_time,
                'start_date': start_date,
                'end_date': end_date,
                'file_size': file_stats.st_size
            })

    reports.sort(key=lambda x: x['created_time'], reverse=True)

    if limit:
        reports = reports[:limit]

    return reports

def parse_tip_report_csv(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

    if len(rows) < 2:
        return None

    is_employee_specific = False
    employee_name = None
    employee_position = None

    if len(rows) > 2 and rows[1] and len(rows[1]) > 1 and rows[1][0] == "Employee":
        is_employee_specific = True
        employee_name = rows[1][1] if len(rows[1]) > 1 else ''
        if len(rows) > 2 and rows[2] and len(rows[2]) > 1 and rows[2][0] == "Position":
            employee_position = rows[2][1]

    report_data = {
        'title': rows[0][0] if rows[0] else 'Employee Tip Report',
        'date_range': '',
        'summary': [],
        'details': [],
        'is_employee_specific': is_employee_specific,
        'employee_name': employee_name,
        'employee_position': employee_position
    }

    if is_employee_specific:
        for i, row in enumerate(rows):
            if row and len(row) > 1 and row[0] == "Date Range":
                report_data['date_range'] = row[1]
            elif row and len(row) > 0 and row[0] == "Summary":
                summary_data = {}
                for j in range(i + 1, len(rows)):
                    if not rows[j] or len(rows[j]) < 2:
                        break
                    key = rows[j][0].strip()
                    value = rows[j][1].strip()
                    if key:
                        summary_data[key] = value

                if summary_data:
                    report_data['summary'].append({
                        'employee_name': employee_name,
                        'position': employee_position,
                        'bank_card_tips': summary_data.get('Total Bank Card Tips', ''),
                        'cash_tips': summary_data.get('Total Cash Tips', ''),
                        'adjustments': summary_data.get('Total Adjustments', ''),
                        'tips_on_paycheck': summary_data.get('Total Tips on Paycheck', ''),
                        'tip_out': summary_data.get('Total Tip Out', ''),
                        'take_home': summary_data.get('Total Take Home', ''),
                        'num_shifts': summary_data.get('Number of Shifts', '')
                    })
                break

        for i, row in enumerate(rows):
            if row and len(row) > 0 and row[0] == "Daily Breakdown":
                if i + 1 < len(rows) and rows[i + 1] and rows[i + 1][0] == "Date":
                    entries = []
                    for j in range(i + 2, len(rows)):
                        if not rows[j] or len(rows[j]) < 10:
                            break
                        if rows[j][0] == "TOTAL":
                            break
                        entries.append({
                            'date': rows[j][0].strip(),
                            'day': rows[j][1].strip() if len(rows[j]) > 1 else '',
                            'bank_card_sales': rows[j][2].strip() if len(rows[j]) > 2 else '',
                            'bank_card_tips': rows[j][3].strip() if len(rows[j]) > 3 else '',
                            'total_sales': rows[j][4].strip() if len(rows[j]) > 4 else '',
                            'cash_tips': rows[j][5].strip() if len(rows[j]) > 5 else '',
                            'adjustments': rows[j][6].strip() if len(rows[j]) > 6 else '',
                            'tips_on_paycheck': rows[j][7].strip() if len(rows[j]) > 7 else '',
                            'tip_out': rows[j][8].strip() if len(rows[j]) > 8 else '',
                            'take_home': rows[j][9].strip() if len(rows[j]) > 9 else ''
                        })

                    if entries:
                        report_data['details'].append({
                            'employee': f"{employee_name} - {employee_position}",
                            'entries': entries
                        })
                break

        return report_data

    report_data['date_range'] = rows[1][1] if len(rows[1]) > 1 else ''

    summary_start = None
    details_start = None

    for i, row in enumerate(rows):
        if row and len(row) > 0 and row[0] == "Employee Name":
            summary_start = i
            print(f"DEBUG: Found summary start at row {i}")
        elif row and len(row) > 0 and "Detailed Daily Breakdown" in str(row[0]):
            details_start = i
            print(f"DEBUG: Found details start at row {i}")
            break

    if summary_start is not None:
        for i in range(summary_start + 1, len(rows)):
            row = rows[i]
            if not row or len(row) == 0:
                break
            if row[0] == '' or 'Detailed' in str(row[0]):
                break
            if len(row) >= 9 and row[0].strip():
                report_data['summary'].append({
                    'employee_name': row[0].strip(),
                    'position': row[1].strip() if len(row) > 1 else '',
                    'bank_card_tips': row[2].strip() if len(row) > 2 else '',
                    'cash_tips': row[3].strip() if len(row) > 3 else '',
                    'adjustments': row[4].strip() if len(row) > 4 else '',
                    'tips_on_paycheck': row[5].strip() if len(row) > 5 else '',
                    'tip_out': row[6].strip() if len(row) > 6 else '',
                    'take_home': row[7].strip() if len(row) > 7 else '',
                    'num_shifts': row[8].strip() if len(row) > 8 else ''
                })

    if details_start is not None:
        current_employee = None
        current_entries = []

        for i in range(details_start + 2, len(rows)):
            row = rows[i]
            if not row or len(row) == 0 or not row[0]:
                if current_employee and current_entries:
                    report_data['details'].append({
                        'employee': current_employee,
                        'entries': current_entries
                    })
                    current_employee = None
                    current_entries = []
                continue

            cell_value = str(row[0]).strip()

            if cell_value.startswith('Employee:'):
                if current_employee and current_entries:
                    report_data['details'].append({
                        'employee': current_employee,
                        'entries': current_entries
                    })
                current_employee = cell_value.replace('Employee: ', '')
                current_entries = []
            elif cell_value == 'Date':
                continue
            elif cell_value == 'TOTAL':
                continue
            elif current_employee and cell_value:
                if len(row) >= 10:
                    current_entries.append({
                        'date': row[0].strip(),
                        'day': row[1].strip() if len(row) > 1 else '',
                        'bank_card_sales': row[2].strip() if len(row) > 2 else '',
                        'bank_card_tips': row[3].strip() if len(row) > 3 else '',
                        'total_sales': row[4].strip() if len(row) > 4 else '',
                        'cash_tips': row[5].strip() if len(row) > 5 else '',
                        'adjustments': row[6].strip() if len(row) > 6 else '',
                        'tips_on_paycheck': row[7].strip() if len(row) > 7 else '',
                        'tip_out': row[8].strip() if len(row) > 8 else '',
                        'take_home': row[9].strip() if len(row) > 9 else ''
                    })

        if current_employee and current_entries:
            report_data['details'].append({
                'employee': current_employee,
                'entries': current_entries
            })

    return report_data

def parse_daily_balance_csv(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

    if len(rows) < 2:
        return None

    report_data = {
        'title': rows[0][0] if rows[0] else 'Consolidated Daily Balance Report',
        'date_range': rows[1][1] if len(rows[1]) > 1 else '',
        'daily_reports': []
    }

    i = 3
    while i < len(rows):
        row = rows[i]

        if row and len(row) > 0 and row[0].startswith('Date: '):
            date_parts = row[0].replace('Date: ', '').split(' - ')
            report_date = date_parts[0] if len(date_parts) > 0 else ''
            day_of_week = date_parts[1] if len(date_parts) > 1 else ''

            daily_report = {
                'date': report_date,
                'day_of_week': day_of_week,
                'notes': '',
                'revenue_items': [],
                'expense_items': [],
                'revenue_total': 0,
                'expense_total': 0,
                'cash_over_under': 0,
                'employees': []
            }

            i += 1

            if i < len(rows) and rows[i] and len(rows[i]) > 1 and rows[i][0] == 'Notes':
                daily_report['notes'] = rows[i][1]
                i += 1

            while i < len(rows) and (not rows[i] or len(rows[i]) == 0 or rows[i][0] == ''):
                i += 1

            if i < len(rows) and rows[i] and rows[i][0] == 'Revenue & Income':
                i += 1
                while i < len(rows) and rows[i] and len(rows[i]) >= 2:
                    if rows[i][0] == 'Total Revenue':
                        daily_report['revenue_total'] = rows[i][1]
                        i += 1
                        break
                    elif rows[i][0] and rows[i][0] not in ['', 'Deposits & Expenses', 'Employee Breakdown']:
                        daily_report['revenue_items'].append({
                            'name': rows[i][0],
                            'value': rows[i][1]
                        })
                    i += 1

            while i < len(rows) and (not rows[i] or len(rows[i]) == 0 or rows[i][0] == ''):
                i += 1

            if i < len(rows) and rows[i] and rows[i][0] == 'Deposits & Expenses':
                i += 1
                while i < len(rows) and rows[i] and len(rows[i]) >= 2:
                    if rows[i][0] == 'Total Expenses':
                        daily_report['expense_total'] = rows[i][1]
                        i += 1
                        break
                    elif rows[i][0] and rows[i][0] not in ['', 'Cash Over/Under', 'Employee Breakdown']:
                        daily_report['expense_items'].append({
                            'name': rows[i][0],
                            'value': rows[i][1]
                        })
                    i += 1

            while i < len(rows) and (not rows[i] or len(rows[i]) == 0 or rows[i][0] == ''):
                i += 1

            if i < len(rows) and rows[i] and rows[i][0] == 'Cash Over/Under':
                daily_report['cash_over_under'] = rows[i][1]
                i += 1

            while i < len(rows) and (not rows[i] or len(rows[i]) == 0 or rows[i][0] == ''):
                i += 1

            if i < len(rows) and rows[i] and rows[i][0] == 'Employee Breakdown':
                i += 1

                if i < len(rows) and rows[i] and rows[i][0] == 'Employee Name':
                    i += 1

                while i < len(rows) and rows[i] and len(rows[i]) >= 10:
                    if rows[i][0] in ['', '=' * 80] or rows[i][0].startswith('Date: '):
                        break

                    daily_report['employees'].append({
                        'name': rows[i][0],
                        'position': rows[i][1],
                        'bank_card_sales': rows[i][2],
                        'bank_card_tips': rows[i][3],
                        'cash_tips': rows[i][4],
                        'total_sales': rows[i][5],
                        'adjustments': rows[i][6],
                        'tips_on_paycheck': rows[i][7],
                        'tip_out': rows[i][8],
                        'take_home': rows[i][9]
                    })
                    i += 1

            report_data['daily_reports'].append(daily_report)

        i += 1

    return report_data
