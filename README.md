# Internal Management System

A web-based internal management application for daily financial tracking, employee tips, and administrative management.

## Technology Stack

- **Backend:** Python 3.8+, FastAPI
- **Frontend:** Jinja2 templates (server-rendered HTML)
- **Database:** SQLite (local file-based)
- **Authentication:** JWT-based (cookie storage)
- **Server Port:** 5710

## Features

- JWT-based authentication with admin roles
- Employee management with scheduling
- Daily financial balance tracking
- Per-employee tip tracking and calculations
- CSV report generation
- Human-readable URLs with slugs
- First-run setup wizard

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. Clone the repository:
```bash
git clone <your-repo-url>
cd sprinance
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python -m app.main
```

Or alternatively:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5710 --reload
```

4. Open your browser and navigate to:
```
http://localhost:5710
```

## First Run Setup

On first launch, you'll be automatically directed to create an admin account:

1. Navigate to `http://localhost:5710`
2. You'll see the "Initial Setup" page
3. Create your administrator username and password
4. Click "Create Admin Account"
5. You'll be automatically logged in

## Application Structure

```
project-root/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database connection and setup
│   ├── models.py               # SQLAlchemy models
│   ├── auth/
│   │   └── jwt_handler.py      # JWT authentication logic
│   ├── routes/
│   │   ├── auth.py             # Login/logout routes
│   │   ├── admin.py            # User management routes
│   │   ├── employees.py        # Employee management routes
│   │   └── daily_balance.py    # Daily balance tracking routes
│   ├── templates/              # Jinja2 HTML templates
│   ├── static/                 # CSS and JavaScript files
│   └── utils/
│       ├── slugify.py          # URL slug generation
│       └── csv_generator.py    # CSV report generation
├── data/
│   ├── database.db             # SQLite database (created on first run)
│   └── reports/                # Generated CSV reports
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Usage Guide

### Landing Page
- Central navigation hub
- Shows current date and day of week
- Links to all main sections

### Administration (Admin Only)
- Create, edit, and delete users
- Assign admin privileges
- Access via `/admin`

### Employee Management
- Create, edit, and delete employees
- Set employee positions (waitstaff, bartender, etc.)
- Configure scheduled work days
- Set tip entry requirements per employee
- Access via `/employees`
- Individual employee pages: `/employees/{slug}`

### Daily Balance
- Primary workflow page for daily financial tracking
- Automatically loads employees scheduled for current day
- Add/remove employees as needed
- Enter daily financial totals:
  - Total cash sales
  - Total card sales
  - Total tips collected
- Enter per-employee tip data (fields based on employee configuration):
  - Bank card sales
  - Bank card tips
  - Cash tips
  - Total sales
  - Adjustments
- **Save Draft** - Save work in progress
- **Generate Report** - Finalize and generate CSV
- Access via `/daily-balance`
- View specific date: `/daily-balance?selected_date=YYYY-MM-DD`

### Report Generation
When you click "Generate Report (Finalize)":
1. The daily balance is locked (marked as finalized)
2. A CSV file is generated
3. CSV is saved to: `data/reports/daily_report/{YEAR}/{MONTH}/YYYY-MM-DD-daily-balance.csv`
   - Reports are automatically organized by year and month
   - Example: `data/reports/daily_report/2026/01/2026-01-12-daily-balance.csv`
4. CSV includes:
   - Date and day of week
   - Daily financial summary
   - Per-employee breakdown with all tip calculations

## URL Structure

All routes use human-readable slugs:
- `/employees/john-smith`
- `/admin/users/jane-admin`
- `/daily-balance?selected_date=2026-01-09`

## Database Models

### User
- username, password_hash, slug, is_admin

### Employee
- name, slug, position, scheduled_days
- requires_bank_card_sales, requires_cash_tips, requires_total_sales

### DailyBalance
- date, day_of_week
- total_cash_sales, total_card_sales, total_tips_collected
- notes, finalized

### DailyEmployeeEntry
- Links to DailyBalance and Employee
- bank_card_sales, bank_card_tips, cash_tips, total_sales
- adjustments, calculated_take_home

## Security Notes

- Passwords are hashed using bcrypt
- JWT tokens are stored in HTTP-only cookies
- Admin-only routes are protected with middleware
- Change the `SECRET_KEY` in `app/auth/jwt_handler.py` for production use

## Development

### Running in Development Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5710 --reload
```

The `--reload` flag enables auto-reloading when you make code changes.

### Database Location
The SQLite database is stored at: `data/database.db`

To reset the database, simply delete this file and restart the application.

## Troubleshooting

**Port already in use:**
```bash
# Find process using port 5710
lsof -i :5710

# Kill the process
kill -9 <PID>
```

**Missing dependencies:**
```bash
pip install -r requirements.txt --upgrade
```

**Database errors:**
Delete the database file and restart:
```bash
rm data/database.db
python -m app.main
```

## License

MIT License