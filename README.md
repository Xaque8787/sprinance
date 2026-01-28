# Daily Dough

**Daily Balance and Tip Records Management System**

A comprehensive web-based application for managing daily financial tracking, employee tips, and administrative operations for restaurants and hospitality businesses.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Technology Stack](#technology-stack)
- [Features](#features)
- [Installation](#installation)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
  - [PyCharm Setup](#pycharm-setup)
- [First Run Setup](#first-run-setup)
- [Usage Guide](#usage-guide)
- [Database Management](#database-management)
- [Email Reports](#email-reports)
- [Docker Deployment](#docker-deployment-guide)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## Overview

Daily Dough is a modern, full-featured management system designed for restaurants and hospitality businesses to track daily finances, manage employee tip distribution, and generate comprehensive reports. Built with Python and FastAPI, it offers a clean, intuitive interface with powerful backend capabilities.

### Technology Stack

- **Backend:** Python 3.8+, FastAPI
- **Frontend:** Jinja2 templates (server-rendered HTML)
- **Database:** SQLite (local file-based)
- **Authentication:** JWT-based (cookie storage)
- **Email:** Resend API for formatted HTML emails
- **Deployment:** Docker with automated migrations
- **Server Port:** 5710

## Quick Start

### 5-Minute Setup

**Option 1: Using Python Directly**
```bash
pip install -r requirements.txt
python run.py
```

**Option 2: Using Docker**
```bash
chmod +x docker-setup.sh
./docker-setup.sh
```

**Option 3: Manual Docker**
```bash
docker-compose -f docker-compose.local.yml up --build -d
```

Then open your browser to: **http://localhost:5710**

## Features

### Core Features
- JWT-based authentication with admin roles
- Employee management with scheduling
- Daily financial balance tracking
- Per-employee tip tracking and calculations
- Comprehensive report generation (CSV and HTML email)
- Human-readable URLs with slugs
- First-run setup wizard
- Real-time take-home tips calculation
- CRUD financial line items (fully customizable)
- Multi-recipient email reports with opt-in preferences
- Automated database migrations

### Financial Management
- **Revenue & Income Tracking:**
  - Cash drawers beginning
  - Food and beverage sales (beer, wine, non-alcoholic)
  - Catering and fundraising contributions
  - Sales tax payable
  - Gift certificates sold
  - Customizable line items

- **Deposits & Expenses:**
  - Gift certificates redeemed
  - Checking account deposits (cash and cards)
  - Cash paid out
  - Cash drawers end
  - Customizable line items

### Employee & Tip Management
- Per-employee tip entry with flexible fields
- Bank card sales and tips tracking
- Cash tips tracking
- Adjustments and corrections
- Tips on paycheck (payroll integration)
- Real-time calculation display
- Position-based tip requirements

### Reports
- **Daily Balance Reports:**
  - Complete financial summary
  - Revenue and expense breakdown
  - Cash over/under calculations
  - Per-employee tip distribution

- **Tip Reports:**
  - Employee summary with totals
  - Daily breakdown per employee
  - Date range filtering
  - Individual employee reports

- **Report Delivery:**
  - CSV file generation
  - HTML email delivery
  - Multiple recipient selection
  - User opt-in preferences

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Docker (optional, for containerized deployment)

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd daily-dough
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5710 --reload
```

4. Open your browser and navigate to:
```
http://localhost:5710
```

### Docker Deployment

#### Local Development with Docker
```bash
docker-compose -f docker-compose.local.yml up --build -d
```

#### Production Deployment

1. Update `.dockerversion` with your version:
```bash
echo "1.0.0" > .dockerversion
```

2. Update `docker-compose.yml` with your registry path:
```yaml
image: ghcr.io/YOUR_GITHUB_USERNAME/daily-dough:latest
```

3. Set environment variables (create `.env` file):
```bash
SECRET_KEY=your-secure-secret-key
RESEND_API_KEY=your-resend-api-key
RESEND_FROM_EMAIL_DAILY=daily@yourdomain.com
RESEND_FROM_EMAIL_TIPS=tips@yourdomain.com
```

4. Deploy:
```bash
docker-compose pull
docker-compose up -d
```

#### Essential Docker Commands

**Local Development:**
```bash
# Start
docker-compose -f docker-compose.local.yml up -d

# Stop
docker-compose -f docker-compose.local.yml down

# Rebuild
docker-compose -f docker-compose.local.yml up --build -d

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Restart
docker-compose -f docker-compose.local.yml restart
```

**Production:**
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Update
docker-compose pull && docker-compose up -d

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

### PyCharm Setup

1. Open PyCharm and select **File → Open**
2. Navigate to your project folder
3. Configure Python Interpreter:
   - **File → Settings → Project → Python Interpreter**
   - Click gear icon ⚙️ → **Add Interpreter → Add Local Interpreter**
   - Choose **Virtualenv Environment → New environment**
   - Set location to `./venv`
   - Click **OK**

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure Run Configuration:
   - **Run → Edit Configurations**
   - Click **+** → **Python**
   - **Name:** Run Server
   - **Script path:** Select `run.py`
   - **Python interpreter:** Select the venv
   - Click **OK**

6. Run the application (green play button ▶️ or `Shift + F10`)

## First Run Setup

On first launch, you'll be automatically directed to create an admin account:

1. Navigate to `http://localhost:5710`
2. You'll see the "Initial Setup" page
3. Create your administrator username and password
4. Click "Create Admin Account"
5. You'll be automatically logged in

## Usage Guide

### Navigation

The application provides five main sections:

1. **Daily Balance** - Track daily financial entries and employee tips
2. **Reports** - View and generate daily balance and tip reports
3. **Employees** - Manage employee information and schedules
4. **Positions** - Configure positions and tip requirements
5. **Administration** - User management and system settings (admin only)

### Daily Balance Entry

1. **Select Date** - Choose the date for entry (defaults to today)
2. **Enter Financial Data:**
   - Revenue & Income items (fully customizable)
   - Deposits & Expenses items (fully customizable)
3. **Add Employees:**
   - Automatically loads scheduled employees for the selected day
   - Add/remove employees as needed
4. **Enter Employee Tips:**
   - Bank Card Sales
   - Bank Card Tips
   - Total Sales
   - Cash Tips
   - Adjustments (if any)
   - Tips on Paycheck (if applicable)
5. **Real-time Calculation:**
   - Take-Home Tips calculate automatically as you type
   - Formula: `Bank Card Tips + Cash Tips + Adjustments - Tips on Paycheck`
6. **Save or Finalize:**
   - **Save Draft** - Save work in progress
   - **Generate Report** - Finalize and create CSV

### Managing Financial Line Items (Admin Only)

1. Navigate to Daily Balance page
2. Click **"⚙ Manage Items"** button in Revenue & Income or Deposits & Expenses section
3. **Add New Item:**
   - Enter item name in the dialog
   - Click "Add Item"
4. **Rename Item:**
   - Click blue "✎" (edit) button
   - Edit the name
   - Click green "✓" (save) or gray "✗" (cancel)
5. **Remove Item:**
   - Click red "×" button
   - Confirm deletion
6. Click button again to exit management mode

### Employee Management

1. Navigate to **Employees** section
2. **Create Employee:**
   - Click "New Employee"
   - Enter name, position, and email
   - Select scheduled work days
   - Configure tip entry requirements
3. **Edit Employee:**
   - Click employee name or "Edit" button
   - Update information
   - Save changes
4. **View Employee Details:**
   - Click employee name
   - View complete profile and tip history

### Position Management

1. Navigate to **Positions** section
2. **Create Position:**
   - Click "New Position"
   - Enter position name
   - Configure tip requirements
3. **Configure Tip Requirements:**
   - Bank Card Sales
   - Bank Card Tips
   - Total Sales
   - Cash Tips
   - Adjustments

### Report Generation

#### Daily Balance Reports

1. Navigate to **Reports → Daily Balance**
2. Select date range
3. Click **Generate Report**
4. Report is saved to: `data/reports/daily_report/{YEAR}/{MONTH}/YYYY-MM-DD-daily-balance.csv`
5. Options:
   - **View** - Display in browser
   - **Download** - Download CSV
   - **Email** - Send via email

#### Tip Reports

1. Navigate to **Reports → Tip Reports**
2. Select date range
3. Select employees (or all)
4. Click **Generate Report**
5. Options:
   - **View** - Display in browser
   - **Download** - Download CSV
   - **Email** - Send via email

#### View All Reports

- Click **"View All"** button to see complete history
- Access all previously generated reports
- View and download any historical report

## Database Management

### Database Location

The SQLite database is stored at: `data/database.db`

### Migrations

The application uses a **database-backed migration system** that tracks applied migrations in the database (not the filesystem).

**Key features:**
- Migrations tracked in `schema_migrations` table
- Migration files are immutable (never moved or deleted)
- Idempotent and safe to run repeatedly
- Automatic on container startup

**Creating a Migration:**

1. Create file in `migrations/` directory with format: `YYYY_MM_DD_description.py`

2. Define `MIGRATION_ID` and `upgrade()` function:

```python
MIGRATION_ID = "2026_01_28_add_email_field"

def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()

    # Defensive check before making changes
    if not column_exists('users', 'email'):
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        print("  ✓ Added email column")
    else:
        print("  ℹ️  email column already exists, skipping")
```

**Running Migrations:**
- Automatic: On Docker container startup
- Manual: `python run_migrations.py`

**Check Migration Status:**
```sql
SELECT * FROM schema_migrations ORDER BY id;
```

**Documentation:**
- See `migrations/README.md` for detailed migration guide
- See `MIGRATION_SYSTEM.md` for system architecture and best practices
- See `migrations/example_*.py.example` for templates

### Backup and Reset

**Backup Database:**
```bash
cp data/database.db data/database.db.backup
```

**Reset Database:**
```bash
rm data/database.db
python run.py
```

**Docker Reset:**
```bash
docker-compose down
rm -rf data/*.db
docker-compose up -d
```

## Email Reports

### Configuration

Create `.env` file with email settings:

```
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL_DAILY=daily@yourdomain.com
RESEND_FROM_EMAIL_TIPS=tips@yourdomain.com
```

**Important:**
- Replace `yourdomain.com` with your verified domain in Resend
- All three variables required for email functionality
- From addresses must be verified in Resend account

### User Opt-In Settings

1. Navigate to **Admin → Users**
2. Edit user
3. Under "Email Report Preferences":
   - Check "Automatically receive Daily Balance Reports"
   - Check "Automatically receive Tip Reports"

Users with opt-in enabled are automatically pre-selected when sending reports.

### Sending Email Reports

1. Navigate to any report (Daily Balance or Tip)
2. Click **"Email"** button
3. In email modal:
   - Select admin users (opted-in users pre-checked)
   - Optionally add custom email address
   - Click **"Send Email"**

Reports are sent as beautifully formatted HTML emails matching the web UI.

## Docker Deployment Guide

### Version Management

Update `.dockerversion` file:
```bash
echo "1.0.1" > .dockerversion
git add .dockerversion
git commit -m "Bump version to 1.0.1"
git push
```

GitHub Actions automatically builds and pushes:
- `latest` tag
- Version-specific tag (e.g., `1.0.1`)

### Health Checks

Docker containers include health checks:
```bash
# Check health
docker ps

# Manual health check
curl http://localhost:5710/
```

### Viewing Logs

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs app
```

## Development

### Project Structure

```
daily-dough/
├── app/                              # Main application package
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry
│   ├── database.py                   # Database configuration
│   ├── models.py                     # SQLAlchemy models
│   ├── auth/                         # Authentication module
│   │   └── jwt_handler.py
│   ├── routes/                       # Route handlers
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── employees.py
│   │   ├── positions.py
│   │   ├── daily_balance.py
│   │   ├── financial_items.py
│   │   ├── reports.py
│   │   └── tip_requirements.py
│   ├── templates/                    # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── setup.html
│   │   ├── admin/
│   │   ├── employees/
│   │   ├── positions/
│   │   ├── daily_balance/
│   │   └── reports/
│   ├── static/                       # Static assets
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── main.js
│   │       └── email_modal.js
│   └── utils/                        # Utility functions
│       ├── slugify.py
│       ├── csv_generator.py
│       ├── csv_reader.py
│       ├── email.py
│       └── backup.py
├── data/                             # Application data
│   ├── database.db                   # SQLite database
│   ├── backups/                      # Database backups
│   └── reports/                      # Generated reports
│       ├── daily_report/
│       └── tip_report/
├── migrations/                       # Database migrations
│   └── old/                          # Archived migrations
├── .dockerversion                    # Docker image version
├── docker-compose.yml                # Production Docker config
├── docker-compose.local.yml          # Local Docker config
├── Dockerfile                        # Docker image definition
├── docker-entrypoint.sh              # Container startup script
├── requirements.txt                  # Python dependencies
├── run.py                            # Quick start script
└── README.md                         # This file
```

### Running in Development Mode

```bash
# With auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 5710 --reload

# Or use run script
python run.py
```

### Database Models

**User**
- username, password_hash, slug, is_admin, email
- opt_in_daily_reports, opt_in_tip_reports

**Employee**
- name, slug, position, scheduled_days, email
- Tip requirement flags

**Position**
- name, slug
- Tip requirement configuration

**DailyBalance**
- date, day_of_week, notes, finalized

**DailyEmployeeEntry**
- Links DailyBalance and Employee
- bank_card_sales, bank_card_tips, cash_tips
- total_sales, adjustments, tips_on_paycheck
- calculated_take_home

**FinancialItemTemplate**
- name, item_type (revenue/expense), is_deduction
- display_order

**FinancialItemValue**
- Links DailyBalance and FinancialItemTemplate
- value (decimal)

## Troubleshooting

### Port Already in Use

**macOS/Linux:**
```bash
lsof -i :5710
kill -9 <PID>
```

**Windows:**
```bash
netstat -ano | findstr :5710
taskkill /PID <process_id> /F
```

### Missing Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### Database Errors

```bash
# Backup first
cp data/database.db data/database.db.backup

# Reset
rm data/database.db
python run.py
```

### Docker Issues

**Container won't start:**
```bash
docker-compose logs
```

**Database issues:**
```bash
# Check data directory
ls -la ./data

# Run migrations manually
docker-compose exec app python /app/run_migrations.py
```

**Health check failing:**
```bash
curl http://localhost:5710/
```

### Email Issues

**No emails being sent:**
1. Check `RESEND_API_KEY` in `.env`
2. Verify from email addresses are configured
3. Ensure from addresses are verified in Resend
4. Check at least one recipient is selected
5. For Docker, verify environment variables in `docker-compose.yml`

**Users not receiving emails:**
1. Verify user has valid email address
2. Check opt-in settings
3. Verify Resend API permissions

### Import Errors in PyCharm

1. **File → Invalidate Caches → Invalidate and Restart**
2. Check Python interpreter configuration
3. Mark project root as "Sources Root"

## Security

### Authentication
- Passwords hashed with bcrypt (never stored plain-text)
- JWT tokens stored in HTTP-only cookies
- Admin routes protected with middleware
- Session management

### Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Use strong, unique admin password
- [ ] Configure HTTPS/SSL
- [ ] Set up proper firewall rules
- [ ] Restrict database file permissions
- [ ] Keep Resend API key secure
- [ ] Never commit `.env` to version control
- [ ] Set up regular database backups
- [ ] Configure monitoring and logging
- [ ] Review user access permissions
- [ ] Update `docker-compose.yml` with registry path
- [ ] Verify email domain settings

### Generate Secure Secret Key

```bash
openssl rand -hex 32
```

### Security Notes

- SQL injection protected by SQLAlchemy ORM
- CSRF-ready architecture
- Email addresses validated server-side
- Only authenticated admins can send reports
- Rate limiting via Resend API
- Environment variables for sensitive data

## Common Commands Reference

### Application Management

```bash
# Start application
python run.py

# Start with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 5710 --reload

# Run migrations
python run_migrations.py

# Verify database column
python verify_column.py
```

### Database Operations

```bash
# Backup database
cp data/database.db data/database.db.backup

# Restore database
cp data/database.db.backup data/database.db

# Reset database
rm data/database.db
```

### Docker Operations

```bash
# Local development
docker-compose -f docker-compose.local.yml up -d
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml logs -f

# Production
docker-compose up -d
docker-compose down
docker-compose pull && docker-compose up -d
docker-compose logs -f
docker-compose restart
```

## File Locations

- **Database:** `data/database.db`
- **Daily Reports:** `data/reports/daily_report/{YEAR}/{MONTH}/`
- **Tip Reports:** `data/reports/tip_report/`
- **Backups:** `data/backups/`
- **Configuration:** `.env`
- **Migrations:** `migrations/`
- **Archive:** `migrations/old/`

## Support Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Jinja2 Documentation:** https://jinja.palletsprojects.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Python Documentation:** https://docs.python.org/3/
- **Docker Documentation:** https://docs.docker.com/
- **Resend Documentation:** https://resend.com/docs

## Future Enhancements

Potential improvements:

- Weekly and monthly report aggregations
- Excel export functionality
- Data visualization and charts
- Multi-location support
- Mobile-responsive improvements
- API endpoints for mobile apps
- Audit logging
- Automated backup scheduling
- Scheduled email delivery
- Report template customization
- Drag-and-drop item reordering
- Advanced filtering and search
- User activity tracking

## License

MIT License

## Version History

See `.dockerversion` for current version.

Major releases:
- **1.0.0** - Initial production release
- **0.0.1** - Initial development version

---

**Daily Dough** - Professional daily balance and tip records management for hospitality businesses.
