import csv
import os
from datetime import datetime
from typing import List, Dict, Any

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

    report_data = {
        'title': rows[0][0] if rows[0] else 'Employee Tip Report',
        'date_range': rows[1][1] if len(rows[1]) > 1 else '',
        'summary': [],
        'details': []
    }

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
