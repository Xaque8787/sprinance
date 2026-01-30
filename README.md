<div align="center">
  <img src="app/static/images/icon-256.png" alt="Daily Dough Logo" width="128" height="128">

  # Daily Dough

  **Professional Daily Balance and Tip Records Management System**

  A comprehensive web-based application for managing daily financial tracking, employee tips, and administrative operations for restaurants and hospitality businesses.

  [![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
  [![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-Framework-teal)](https://fastapi.tiangolo.com/)
  [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
  - [PyCharm Setup](#pycharm-setup)
- [First Run Setup](#first-run-setup)
- [Usage Guide](#usage-guide)
- [Database & Migrations](#database--migrations)
- [Email Configuration](#email-configuration)
- [Project Structure](#project-structure)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Version Management](#version-management)

---

## Overview

**Daily Dough** is a modern, self-hosted management system designed specifically for restaurants and hospitality businesses. It provides comprehensive tools for tracking daily finances, managing employee tip distribution, and generating detailed reports—all through an intuitive web interface.

Built with **Python** and **FastAPI**, Daily Dough combines the performance of modern async Python with the simplicity of server-rendered templates. The application is fully containerized with Docker and includes automated database migrations, making deployment and updates seamless.

### Why Daily Dough?

- **Self-Hosted** - Complete control over your data
- **No Recurring Fees** - One-time setup, no subscriptions
- **Automated Migrations** - Updates apply automatically
- **Email Reports** - Beautiful HTML emails with CSV exports
- **Flexible Configuration** - Fully customizable financial line items
- **Multi-Position Support** - Handle complex staffing scenarios
- **Audit Trail** - Complete history of all entries and reports

---

## Quick Start

### 5-Minute Setup

**Option 1: Python Directly**
```bash
pip install -r requirements.txt
python run.py
# Open http://localhost:5710
```

**Option 2: Quick Docker Setup**
```bash
chmod +x docker-setup.sh
./docker-setup.sh
# Open http://localhost:5710
```

**Option 3: Manual Docker**
```bash
docker-compose -f docker-compose.local.yml up --build -d
# Open http://localhost:5710
```

On first launch, you'll be guided through creating an admin account. No complex configuration required to get started!

---

## Key Features

### 📊 Financial Management

- **Revenue & Income Tracking**
  - Cash drawers (beginning/end)
  - Food and beverage sales (beer, wine, non-alcoholic)
  - Catering and fundraising
  - Sales tax payable
  - Gift certificates sold/redeemed
  - **Fully customizable line items** (add/edit/remove as needed)

- **Deposits & Expenses**
  - Checking account deposits (cash and card)
  - Cash paid out tracking
  - Custom expense categories
  - Real-time balance calculations

### 👥 Employee & Tip Management

- **Employee Profiles**
  - Multi-position support
  - Flexible scheduling (by day of week)
  - Email notifications
  - Complete tip history
  - Active/inactive status

- **Tip Calculations**
  - Bank card sales and tips
  - Cash tips tracking
  - Adjustments and corrections
  - Tips on paycheck (payroll integration)
  - Real-time take-home calculation
  - Position-based tip requirements

### 📈 Reporting & Analytics

- **Daily Balance Reports**
  - Complete financial summary
  - Revenue and expense breakdown
  - Cash over/under calculations
  - Per-employee tip distribution
  - Historical report viewing

- **Tip Reports**
  - Employee summary with totals
  - Daily breakdown per employee
  - Date range filtering
  - Individual employee details

- **Report Delivery**
  - CSV file generation
  - HTML email with beautiful formatting
  - Multiple recipient selection
  - User opt-in preferences
  - Automatic scheduling ready

### 🔒 Security & Administration

- **Authentication**
  - JWT-based authentication
  - Bcrypt password hashing
  - HTTP-only cookies
  - Role-based access control (admin/user)

- **Admin Features**
  - User management
  - Email preferences
  - Financial item configuration
  - Position and tip requirement setup
  - Database migration management

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python 3.8+, FastAPI | High-performance async web framework |
| **Frontend** | Jinja2 Templates | Server-rendered HTML for simplicity |
| **Database** | SQLite | File-based, zero-configuration database |
| **ORM** | SQLAlchemy | Database abstraction and migrations |
| **Authentication** | JWT (python-jose) | Secure token-based auth |
| **Passwords** | bcrypt | Industry-standard password hashing |
| **Email** | Resend API | Reliable email delivery |
| **Containerization** | Docker | Consistent deployment everywhere |
| **Automation** | GitHub Actions | CI/CD for Docker images |
| **Port** | 5710 | Default application port |

---

## Installation

### Prerequisites

- **Python 3.8+** (for local development)
- **pip** (Python package manager)
- **Docker** (optional, for containerized deployment)
- **Git** (for version control)

### Local Development

Perfect for development, testing, or single-machine deployments:

```bash
# 1. Clone repository
git clone <your-repo-url>
cd daily-dough

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run application
python run.py

# Or with auto-reload for development:
uvicorn app.main:app --host 0.0.0.0 --port 5710 --reload

# 4. Access application
# Open browser to http://localhost:5710
```

The application will:
1. Create a SQLite database at `data/database.db`
2. Run any pending migrations
3. Start the web server
4. Redirect you to initial setup

### Docker Deployment

Recommended for production and easy updates:

#### Local Development with Docker

```bash
# Start containers
docker-compose -f docker-compose.local.yml up --build -d

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Stop containers
docker-compose -f docker-compose.local.yml down
```

#### Production Deployment

1. **Set Version**
   ```bash
   echo "1.0.0" > .dockerversion
   ```

2. **Configure Docker Compose**

   Edit `docker-compose.yml` to use your Docker registry:
   ```yaml
   image: ghcr.io/YOUR_GITHUB_USERNAME/daily-dough:latest
   ```

3. **Set Environment Variables**

   Create `.env` file:
   ```env
   SECRET_KEY=your-secure-secret-key-here
   RESEND_API_KEY=re_your_resend_api_key
   RESEND_FROM_EMAIL_DAILY=daily@yourdomain.com
   RESEND_FROM_EMAIL_TIPS=tips@yourdomain.com
   ```

4. **Deploy**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

5. **Verify**
   ```bash
   docker-compose ps
   docker-compose logs
   curl http://localhost:5710
   ```

#### Essential Docker Commands

```bash
# Local Development
docker-compose -f docker-compose.local.yml up -d        # Start
docker-compose -f docker-compose.local.yml down         # Stop
docker-compose -f docker-compose.local.yml restart      # Restart
docker-compose -f docker-compose.local.yml logs -f      # View logs
docker-compose -f docker-compose.local.yml up --build   # Rebuild

# Production
docker-compose up -d                                    # Start
docker-compose down                                     # Stop
docker-compose restart                                  # Restart
docker-compose logs -f                                  # View logs
docker-compose pull && docker-compose up -d             # Update
```

### PyCharm Setup

For developers using PyCharm IDE:

1. **Open Project**
   - File → Open → Select project directory

2. **Configure Python Interpreter**
   - File → Settings → Project → Python Interpreter
   - Click ⚙️ → Add Interpreter → Add Local Interpreter
   - Select "Virtualenv Environment" → "New environment"
   - Location: `./venv`
   - Click OK

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create Run Configuration**
   - Run → Edit Configurations → Click +
   - Select "Python"
   - Name: "Run Server"
   - Script path: `<project-dir>/run.py`
   - Python interpreter: Select your venv
   - Click OK

5. **Run Application**
   - Click green play button ▶️ or press `Shift + F10`

---

## First Run Setup

When you first access the application, you'll be automatically redirected to the setup wizard:

1. **Navigate to Application**
   - Open browser to `http://localhost:5710`

2. **Initial Setup Page**
   - You'll see "Welcome to Daily Dough - Initial Setup"
   - Enter desired admin username
   - Enter secure password
   - Confirm password

3. **Create Account**
   - Click "Create Admin Account"
   - You'll be automatically logged in
   - Redirected to the home dashboard

4. **Post-Setup Configuration**
   - Add employees (Employees → New Employee)
   - Configure positions (Positions → New Position)
   - Customize financial items (Daily Balance → ⚙ Manage Items)
   - Set up email reports (Admin → Users → Edit → Email Preferences)

---

## Usage Guide

### Navigation Structure

The application provides five main sections accessible from the top navigation:

1. **🏠 Home** - Dashboard and quick links
2. **💰 Daily Balance** - Create and manage daily financial entries
3. **📊 Reports** - View, generate, and email reports
4. **👥 Employees** - Manage employee profiles and schedules
5. **🎯 Positions** - Configure positions and tip requirements
6. **⚙️ Administration** - User management and system settings (admin only)

### Daily Balance Entry

Complete workflow for recording a day's financial data:

#### Step 1: Select Date
- Choose the date for your entry (defaults to today)
- System loads any existing entry for that date
- Shows scheduled employees for that day

#### Step 2: Enter Financial Data

**Revenue & Income Section:**
- Cash Drawers Beginning
- Food Sales
- Beer Sales
- Wine Sales
- Non-Alcoholic Beverage Sales
- Catering
- Fundraising
- Sales Tax Payable
- Gift Certificates Sold
- Custom items (add via ⚙ Manage Items)

**Deposits & Expenses Section:**
- Gift Certificates Redeemed
- Checking Deposits (Cash)
- Checking Deposits (Card)
- Cash Paid Out
- Cash Drawers End
- Custom items (add via ⚙ Manage Items)

#### Step 3: Configure Employees
- System automatically loads employees scheduled for selected day
- Click "+ Add Employee" to add additional staff
- Click "Remove" to remove employees who didn't work
- Each employee can work under a specific position

#### Step 4: Enter Tip Data

For each employee, enter:
- **Bank Card Sales** - Total credit/debit sales
- **Bank Card Tips** - Tips from credit/debit cards
- **Total Sales** - Combined cash and card sales (if tracked separately)
- **Cash Tips** - Tips received in cash
- **Adjustments** - Any corrections or special adjustments
- **Tips on Paycheck** - Tips to be added to payroll instead of cash

**Real-time Calculation:**
The system automatically calculates take-home tips as you type:
```
Take Home = Bank Card Tips + Cash Tips + Adjustments - Tips on Paycheck
```

#### Step 5: Save or Generate Report

- **Save Draft** - Save your work without finalizing
  - Allows editing later
  - Not included in reports until finalized

- **Generate Report** - Finalize the entry
  - Marks entry as finalized
  - Generates CSV report
  - Saves to `data/reports/daily_report/YYYY/MM/`
  - Entry becomes read-only (prevents accidental changes)

### Managing Financial Line Items

Customize revenue and expense categories to match your business:

1. Navigate to **Daily Balance** page
2. Click **"⚙ Manage Items"** in Revenue or Expenses section
3. Management mode activates (button turns red)

**Add New Item:**
- Click "+ Add Item" button
- Enter item name in dialog
- Click "Add Item" to save
- New item appears at bottom of list

**Edit Item:**
- Click blue **✎** (edit) icon next to item name
- Field becomes editable
- Modify the name
- Click green **✓** to save or gray **✗** to cancel

**Remove Item:**
- Click red **×** button next to item
- Confirm deletion
- Item is permanently removed
- Historical data using this item remains intact

**Exit Management Mode:**
- Click **"⚙ Manage Items"** button again
- Returns to normal entry mode

### Employee Management

#### Creating an Employee

1. Navigate to **Employees** section
2. Click **"New Employee"** button
3. Fill in details:
   - **First Name** - Employee's first name
   - **Last Name** - Employee's last name
   - **Email** - For receiving tip reports (optional)
   - **Position** - Select default position
   - **Scheduled Days** - Check days they typically work
   - **Is Active** - Checked by default (uncheck to deactivate)

4. Configure tip requirements:
   - Check which tip fields are required for this employee
   - Matches position requirements by default
   - Can be customized per employee

5. Click **"Save Employee"**

#### Editing an Employee

1. Click employee name or **Edit** button
2. Modify any field
3. Save changes
4. Changes apply to future entries only (history preserved)

#### Viewing Employee History

1. Click employee name in list
2. View complete profile:
   - Basic information
   - Position and schedule
   - Tip history (all entries)
   - Total tips earned
   - Average tips per shift

### Position Management

Positions define job roles and their associated tip tracking requirements.

#### Creating a Position

1. Navigate to **Positions** section
2. Click **"New Position"** button
3. Enter position name (e.g., "Server", "Bartender", "Busser")
4. Configure tip requirements:
   - **Bank Card Sales** - Track credit/debit sales
   - **Bank Card Tips** - Track card tips
   - **Total Sales** - Track combined sales
   - **Cash Tips** - Track cash tips
   - **Adjustments** - Allow adjustments

5. Click **"Save Position"**

Employees assigned to this position will inherit these requirements by default (but can be customized per employee).

### Report Generation

#### Daily Balance Reports

Complete financial summary for a specific date:

1. Navigate to **Reports → Daily Balance**
2. Click date selector
3. Select desired date
4. Click **"Generate Report"**

Report includes:
- All revenue and income items
- All deposit and expense items
- Total calculations
- Cash over/under
- Per-employee tip breakdown
- Summary totals

**Actions:**
- **View** - Display in browser
- **Download** - Download CSV file
- **Email** - Send to recipients

#### Tip Reports

Employee tip summary for date range:

1. Navigate to **Reports → Tip Reports**
2. Select **Start Date**
3. Select **End Date**
4. Select employees:
   - Check "All Employees" for everyone
   - Or select specific employees
5. Click **"Generate Report"**

Report includes:
- Per-employee summary with totals
- Daily breakdown for each employee
- Grand totals for date range
- Average tips per shift

**Actions:**
- **View** - Display in browser
- **Download** - Download CSV file
- **Email** - Send to recipients

#### Viewing Historical Reports

Access all previously generated reports:

1. Navigate to desired report section
2. Click **"View All"** button
3. Browse list of saved reports
4. Click report name to view
5. Download or email from report view

Reports are organized by:
- **Daily Reports**: `data/reports/daily_report/YYYY/MM/`
- **Tip Reports**: `data/reports/tip_report/`

---

## Database & Migrations

### Database Overview

**Daily Dough** uses SQLite for data persistence, providing:
- Zero configuration required
- Single file database (`data/database.db`)
- ACID compliance
- Cross-platform compatibility
- Easy backup (just copy the file)

### Migration System

The application uses a **database-backed migration system** that ensures schema changes are applied consistently across all deployments.

#### How It Works

1. **Database Tracking**: Migrations are tracked in the `schema_migrations` table
2. **Immutable Files**: Migration files never move or change after creation
3. **Automatic Execution**: Runs on every container startup
4. **Idempotent**: Safe to run repeatedly (checks before applying)
5. **Transactional**: Automatic rollback on failure

#### Migration Table Schema

```sql
CREATE TABLE schema_migrations (
    id TEXT PRIMARY KEY,              -- e.g., "2026_01_28_add_email_field"
    applied_at TIMESTAMP NOT NULL     -- ISO 8601 timestamp
);
```

#### Migration Lifecycle

```
Developer Creates Migration
         ↓
File Added to /migrations
         ↓
Commit & Push to Git
         ↓
Docker Image Built (CI/CD)
         ↓
Container Starts
         ↓
run_migrations.py Executes
         ↓
Checks schema_migrations Table
         ↓
Applies Pending Migrations
         ↓
Records Success
         ↓
Application Starts
```

### Creating a Migration

#### Step 1: Create Migration File

```bash
touch migrations/2026_01_28_add_employee_email.py
```

**Naming Convention**: `YYYY_MM_DD_description.py`

#### Step 2: Define Migration

```python
"""
Add email field to employees table

This migration adds an optional email field to support
email notifications and tip report delivery.
"""

MIGRATION_ID = "2026_01_28_add_employee_email"


def upgrade(conn, column_exists, table_exists):
    """
    Add email column to employees table.

    Args:
        conn: SQLite database connection
        column_exists: Helper function - column_exists(table, column) -> bool
        table_exists: Helper function - table_exists(table) -> bool
    """
    cursor = conn.cursor()

    # Defensive check: only add if column doesn't exist
    if not column_exists('employees', 'email'):
        cursor.execute("""
            ALTER TABLE employees
            ADD COLUMN email TEXT
        """)
        print("  ✓ Added email column to employees table")
    else:
        print("  ℹ️  email column already exists, skipping")
```

#### Step 3: Test Locally

```bash
# Run migration
python run_migrations.py

# Expected output:
# ✓ schema_migrations table ready
# ✓ Discovered 1 migration file(s)
# ▶️  Applying: 2026_01_28_add_employee_email
#   ✓ Added email column to employees table
#   ✅ Success
# ✅ All migrations applied successfully!

# Test idempotency (run again)
python run_migrations.py

# Expected output:
# ✅ All migrations already applied. Database is up to date.
```

#### Step 4: Deploy

Commit and deploy. Docker containers automatically run migrations on startup.

### Migration Patterns

#### Adding a Column

```python
MIGRATION_ID = "2026_01_28_add_user_email"

def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()

    if not column_exists('users', 'email'):
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN email TEXT
        """)
        print("  ✓ Added email column")
```

#### Creating a Table

```python
MIGRATION_ID = "2026_01_28_create_audit_log"

def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()

    if not table_exists('audit_log'):
        cursor.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("  ✓ Created audit_log table")
```

#### Migrating Data

```python
MIGRATION_ID = "2026_01_28_populate_employee_slugs"

def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()

    # Add slug column if it doesn't exist
    if not column_exists('employees', 'slug'):
        cursor.execute("ALTER TABLE employees ADD COLUMN slug TEXT")
        print("  ✓ Added slug column")

    # Populate slugs for employees without one
    cursor.execute("SELECT id, name FROM employees WHERE slug IS NULL")
    employees = cursor.fetchall()

    for emp_id, name in employees:
        from app.utils.slugify import slugify
        slug = slugify(name)
        cursor.execute("UPDATE employees SET slug = ? WHERE id = ?", (slug, emp_id))

    print(f"  ✓ Populated {len(employees)} employee slugs")
```

#### Recreating a Table (SQLite Limitation)

SQLite doesn't support all ALTER TABLE operations. To modify column types or constraints:

```python
MIGRATION_ID = "2026_01_28_make_position_nullable"

def upgrade(conn, column_exists, table_exists):
    cursor = conn.cursor()

    # Check if we need to recreate
    cursor.execute("SELECT sql FROM sqlite_master WHERE name='employees'")
    table_sql = cursor.fetchone()[0]

    if 'position_id INTEGER NOT NULL' in table_sql:
        print("  ✓ Recreating employees table to make position_id nullable")

        # Create new table with updated schema
        cursor.execute("""
            CREATE TABLE employees_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                position_id INTEGER,  -- Now nullable
                email TEXT,
                FOREIGN KEY (position_id) REFERENCES positions(id)
            )
        """)

        # Copy data
        cursor.execute("""
            INSERT INTO employees_new
            SELECT id, name, slug, position_id, email
            FROM employees
        """)

        # Replace old table
        cursor.execute("DROP TABLE employees")
        cursor.execute("ALTER TABLE employees_new RENAME TO employees")

        print("  ✓ Table recreated successfully")
    else:
        print("  ℹ️  position_id is already nullable")
```

### Helper Functions

The migration runner provides built-in helpers:

#### `column_exists(table_name, column_name)`

Check if a column exists before adding it:

```python
if not column_exists('users', 'email'):
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
```

#### `table_exists(table_name)`

Check if a table exists before creating it:

```python
if not table_exists('audit_log'):
    cursor.execute("CREATE TABLE audit_log (...)")
```

These helpers use SQLite's `PRAGMA table_info()` and `sqlite_master` table to inspect the database schema.

### Migration Best Practices

1. **Always Use Defensive Checks**
   ```python
   # ✅ Good - idempotent
   if not column_exists('users', 'email'):
       cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")

   # ❌ Bad - fails on second run
   cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
   ```

2. **Use Descriptive IDs**
   ```python
   # ✅ Good - clear and sortable
   MIGRATION_ID = "2026_01_28_add_employee_email"

   # ❌ Bad - ambiguous
   MIGRATION_ID = "migration_1"
   ```

3. **Document Your Changes**
   ```python
   """
   Add employee snapshot fields for historical preservation

   This migration adds snapshot columns that preserve employee
   and position names even after deletion, ensuring report accuracy.

   Tables affected:
   - daily_employee_entries (adds employee_name_snapshot)
   - daily_financial_line_items (adds employee_name_snapshot)
   """
   ```

4. **Handle Data Migration Carefully**
   ```python
   # Don't overwrite existing data
   cursor.execute("""
       UPDATE employees
       SET slug = ?
       WHERE id = ? AND slug IS NULL
   """, (slug, emp_id))
   ```

5. **Test Locally First**
   - Always test on a copy of production data
   - Run migration at least twice (test idempotency)
   - Verify data integrity after migration

6. **Keep Migrations Small**
   - One logical change per migration
   - Easier to debug if something goes wrong
   - Clearer history

### Running Migrations

#### Automatic (Docker)

Migrations run automatically on container startup via `docker-entrypoint.sh`:

```bash
# Build and start container
docker-compose up -d

# Migrations run automatically
# Check logs to verify:
docker-compose logs | grep migration
```

#### Manual (Development)

```bash
# Run all pending migrations
python run_migrations.py

# Check migration status
python -c "
import sqlite3
conn = sqlite3.connect('data/database.db')
for row in conn.execute('SELECT * FROM schema_migrations ORDER BY id'):
    print(row)
"
```

### Checking Migration Status

View applied migrations in the database:

```sql
SELECT id, applied_at
FROM schema_migrations
ORDER BY applied_at;
```

Or using Python:

```python
import sqlite3
conn = sqlite3.connect('data/database.db')
cursor = conn.execute("SELECT id, applied_at FROM schema_migrations ORDER BY id")
for migration_id, applied_at in cursor:
    print(f"{migration_id} applied at {applied_at}")
```

### Troubleshooting Migrations

#### Migration Recorded But Change Not Present

**Symptoms**: Migration appears in `schema_migrations` but change isn't in database

**Causes**:
- Migration had a bug
- Database was manually modified
- Transaction committed but change failed

**Solution**: Create a new migration with the needed changes. Don't modify the original migration or manually edit `schema_migrations`.

#### Migration Fails Mid-Execution

**Symptoms**: Error during migration, application won't start

**What Happens**:
- Transaction automatically rolls back
- Migration NOT recorded in `schema_migrations`
- Database remains in pre-migration state

**Solution**:
1. Read error message carefully
2. Fix the migration file
3. Test locally
4. Restart container (migration will retry)

#### Need to Skip a Migration

**When**: Migration applied manually outside the migration system

**Solution**: Manually insert into `schema_migrations`:

```sql
INSERT INTO schema_migrations (id, applied_at)
VALUES ('2026_01_28_problematic_migration', datetime('now'));
```

**⚠️ Warning**: Only do this if you've manually applied the exact changes the migration would have made.

#### Need to Re-Run a Migration

**When**: Migration was applied incorrectly and needs to run again

**Solution**:

1. Remove from tracking table:
   ```sql
   DELETE FROM schema_migrations WHERE id = '2026_01_28_migration_name';
   ```

2. Restart application:
   ```bash
   docker-compose restart
   # Or
   python run_migrations.py
   ```

**⚠️ Warning**: Only do this if the migration is truly idempotent (has defensive checks).

### Migration Documentation

- **Full Guide**: `migrations/README.md` - Comprehensive migration documentation
- **Quick Reference**: `migrations/QUICK_START.md` - Common patterns and templates
- **Examples**: `migrations/example_*.py.example` - Copy-paste templates
- **Runner**: `run_migrations.py` - Migration execution logic

### Database Backup and Restore

#### Backup Database

```bash
# Simple file copy (application can be running)
cp data/database.db data/database.db.backup

# With timestamp
cp data/database.db data/database.db.$(date +%Y%m%d_%H%M%S)

# Using SQLite's backup command (safer for active database)
sqlite3 data/database.db ".backup data/database.db.backup"
```

#### Restore Database

```bash
# Stop application first
docker-compose down
# Or kill Python process

# Restore backup
cp data/database.db.backup data/database.db

# Start application
docker-compose up -d
```

#### Automated Backups

Consider setting up a cron job for regular backups:

```bash
# Example cron entry (daily at 2 AM)
0 2 * * * cp /path/to/daily-dough/data/database.db /path/to/backups/database.db.$(date +\%Y\%m\%d)
```

#### Reset Database

**⚠️ Warning**: This deletes all data!

```bash
# Stop application
docker-compose down

# Remove database
rm data/database.db

# Start application (creates fresh database)
docker-compose up -d
```

The application will:
1. Create new database with current schema
2. Run all migrations
3. Redirect to initial setup

---

## Email Configuration

### Overview

Daily Dough uses [Resend](https://resend.com/) for reliable email delivery. Reports can be sent as beautifully formatted HTML emails with CSV attachments.

### Setup

#### 1. Get Resend API Key

1. Sign up at [resend.com](https://resend.com/)
2. Verify your domain (required for production)
3. Navigate to **API Keys** section
4. Create new API key
5. Copy the key (starts with `re_`)

#### 2. Configure Environment Variables

Create `.env` file in project root:

```env
# Required: Resend API key
RESEND_API_KEY=re_your_actual_api_key_here

# Required: From addresses (must be verified in Resend)
RESEND_FROM_EMAIL_DAILY=daily@yourdomain.com
RESEND_FROM_EMAIL_TIPS=tips@yourdomain.com

# Required: JWT secret key
SECRET_KEY=your-secure-secret-key-here
```

**Important Notes**:
- All three `RESEND_*` variables are required for email functionality
- From addresses must be verified in your Resend account
- Use your actual domain (not example.com)
- For development, Resend provides a sandbox domain

#### 3. Verify Domain (Production Only)

For production use, verify your domain in Resend:

1. Log into Resend dashboard
2. Navigate to **Domains** section
3. Click **Add Domain**
4. Follow DNS verification steps
5. Wait for verification (usually minutes)

For development/testing, you can use Resend's provided sandbox domain.

### User Email Preferences

Configure which users receive automatic report notifications:

1. Navigate to **Admin → Users**
2. Click **Edit** on desired user
3. Scroll to **Email Report Preferences**
4. Check preferences:
   - ☐ **Automatically receive Daily Balance Reports**
   - ☐ **Automatically receive Tip Reports**
5. Click **Save User**

Users with preferences enabled will be automatically pre-selected when sending reports via email.

### Sending Email Reports

#### Daily Balance Report

1. Generate or view a daily balance report
2. Click **"Email Report"** button
3. In the email modal:
   - **Recipients**: Admin users with opt-in preferences are pre-checked
   - **Custom Email**: Optionally add additional email address
   - **Subject**: Auto-generated (e.g., "Daily Balance Report - January 28, 2026")
4. Click **"Send Email"**
5. Confirmation message appears

#### Tip Report

1. Generate or view a tip report
2. Click **"Email Report"** button
3. In the email modal:
   - **Recipients**: Admin users with opt-in preferences are pre-checked
   - **Custom Email**: Optionally add additional email address
   - **Subject**: Auto-generated (e.g., "Tip Report - January 20 to January 28, 2026")
4. Click **"Send Email"**
5. Confirmation message appears

### Email Format

Reports are sent as beautiful HTML emails that match the web interface:

- **Subject**: Descriptive, includes report type and date(s)
- **Body**: Full HTML table with all report data
- **Attachment**: CSV file for spreadsheet import
- **Styling**: Professional formatting with proper typography
- **From Name**: "Daily Dough" (customizable in code)
- **From Address**: Configured via environment variables

### Troubleshooting Email

#### No Emails Being Sent

**Check Environment Variables**:
```bash
# For local
cat .env | grep RESEND

# For Docker
docker-compose exec app env | grep RESEND
```

**Verify Configuration**:
- `RESEND_API_KEY` is set and correct
- From email addresses are configured
- From addresses are verified in Resend account

**Check Application Logs**:
```bash
docker-compose logs | grep -i email
# Or
docker-compose logs | grep -i resend
```

#### Users Not Receiving Emails

**Verify User Settings**:
1. Admin → Users → Edit User
2. Check that email address is valid
3. Confirm opt-in preferences are enabled

**Check Spam Folder**:
- Some email providers may filter automated emails
- Recommend adding sender to safe senders list

**Verify Resend Dashboard**:
- Log into Resend
- Check **Emails** section for delivery status
- Look for bounce or error messages

#### Email Delivery Failures

**Domain Not Verified**:
- Verify domain in Resend dashboard
- Ensure DNS records are correctly configured
- Wait for propagation (can take up to 48 hours)

**API Key Invalid**:
- Regenerate API key in Resend
- Update `.env` file
- Restart application

**Rate Limiting**:
- Resend has rate limits based on your plan
- Check your Resend dashboard for limits
- Consider spacing out large email batches

---

## Project Structure

```
daily-dough/
├── app/                                 # Main application package
│   ├── __init__.py                      # Package initialization
│   ├── main.py                          # FastAPI application entry point
│   ├── database.py                      # Database configuration & init_db()
│   ├── models.py                        # SQLAlchemy ORM models
│   ├── scheduler.py                     # Background task scheduler
│   │
│   ├── auth/                            # Authentication module
│   │   ├── __init__.py
│   │   └── jwt_handler.py               # JWT token generation & validation
│   │
│   ├── routes/                          # HTTP route handlers
│   │   ├── __init__.py
│   │   ├── auth.py                      # Login, logout, setup
│   │   ├── admin.py                     # User management (admin only)
│   │   ├── employees.py                 # Employee CRUD
│   │   ├── positions.py                 # Position CRUD
│   │   ├── daily_balance.py             # Daily balance entry & viewing
│   │   ├── financial_items.py           # Financial item CRUD (admin only)
│   │   ├── reports.py                   # Report generation & viewing
│   │   ├── scheduled_tasks.py           # Scheduled task management
│   │   └── tip_requirements.py          # Tip requirement configuration
│   │
│   ├── services/                        # Business logic services
│   │   ├── __init__.py
│   │   └── scheduler_tasks.py           # Scheduled background tasks
│   │
│   ├── templates/                       # Jinja2 HTML templates
│   │   ├── base.html                    # Base template (navigation, auth)
│   │   ├── index.html                   # Home page / dashboard
│   │   ├── login.html                   # Login page
│   │   ├── setup.html                   # Initial setup wizard
│   │   │
│   │   ├── admin/                       # Admin section templates
│   │   │   ├── users.html               # User list
│   │   │   └── user_form.html           # User create/edit form
│   │   │
│   │   ├── employees/                   # Employee section templates
│   │   │   ├── list.html                # Employee list
│   │   │   ├── form.html                # Employee create/edit form
│   │   │   └── detail.html              # Employee detail & history
│   │   │
│   │   ├── positions/                   # Position section templates
│   │   │   ├── list.html                # Position list
│   │   │   └── form.html                # Position create/edit form
│   │   │
│   │   ├── daily_balance/               # Daily balance templates
│   │   │   └── form.html                # Daily balance entry form
│   │   │
│   │   ├── reports/                     # Report templates
│   │   │   ├── index.html               # Reports home
│   │   │   ├── daily_balance_list.html  # Daily balance report form
│   │   │   ├── tip_report_list.html     # Tip report form
│   │   │   ├── saved_daily_balance_reports.html
│   │   │   ├── saved_tip_reports.html
│   │   │   ├── view_saved_daily_balance_report.html
│   │   │   ├── view_saved_tip_report.html
│   │   │   └── employee_tip_detail.html
│   │   │
│   │   └── scheduled_tasks/             # Scheduled tasks templates
│   │       └── index.html               # Task list & management
│   │
│   ├── static/                          # Static assets (CSS, JS, images)
│   │   ├── css/
│   │   │   └── style.css                # Application stylesheet
│   │   ├── js/
│   │   │   ├── main.js                  # Main JavaScript functionality
│   │   │   └── email_modal.js           # Email modal functionality
│   │   └── images/                      # Icons and images
│   │       ├── favicon.ico
│   │       ├── icon-16.png              # PWA icons (multiple sizes)
│   │       ├── icon-32.png
│   │       ├── icon-48.png
│   │       ├── icon-64.png
│   │       ├── icon-128.png
│   │       ├── icon-180.png
│   │       ├── icon-192.png
│   │       ├── icon-256.png
│   │       └── icon-512.png
│   │
│   └── utils/                           # Utility functions
│       ├── __init__.py
│       ├── slugify.py                   # URL-friendly slug generation
│       ├── csv_generator.py             # CSV report generation
│       ├── csv_reader.py                # CSV parsing utilities
│       ├── email.py                     # Email sending via Resend API
│       ├── backup.py                    # Database backup utilities
│       └── version.py                   # Version number utilities
│
├── data/                                # Application data (created at runtime)
│   ├── database.db                      # SQLite database file
│   ├── backups/                         # Database backups
│   │   └── .gitkeep
│   ├── reports/                         # Generated reports
│   │   ├── daily_report/                # Daily balance reports
│   │   │   └── {YEAR}/{MONTH}/          # Organized by date
│   │   └── tip_report/                  # Tip reports
│   └── scheduler/                       # Scheduler state
│       └── .gitkeep
│
├── migrations/                          # Database migrations
│   ├── README.md                        # Migration system guide
│   ├── QUICK_START.md                   # Quick reference
│   ├── .gitkeep                         # Keep directory in git
│   ├── example_2026_01_28_add_column.py.example
│   ├── example_2026_01_28_create_table.py.example
│   ├── example_2026_01_28_data_migration.py.example
│   ├── example_2026_01_28_recreate_table.py.example
│   │
│   └── old/                             # Archived old migrations
│       ├── ARCHIVED.md                  # Explanation of archived files
│       └── *.py                         # Old migration files (reference only)
│
├── .github/                             # GitHub-specific files
│   └── workflows/
│       └── docker-build.yml             # CI/CD: Build & push Docker images
│
├── .dockerversion                       # Current version (for Docker tagging)
├── .env                                 # Environment variables (NOT in git)
├── .gitignore                           # Git ignore rules
├── docker-compose.yml                   # Production Docker Compose config
├── docker-compose.local.yml             # Local development Docker config
├── Dockerfile                           # Docker image definition
├── docker-entrypoint.sh                 # Container startup script
├── docker-setup.sh                      # Quick setup script
├── example.env                          # Example environment variables
├── requirements.txt                     # Python dependencies
├── run_migrations.py                    # Migration runner
├── run.py                               # Quick start script (local dev)
└── README.md                            # This file
```

### Key Directories

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `app/` | Main application code | All Python application code |
| `app/routes/` | HTTP endpoints | FastAPI route handlers |
| `app/templates/` | HTML templates | Jinja2 server-side rendering |
| `app/static/` | CSS, JS, images | Served directly by FastAPI |
| `app/utils/` | Helper functions | Reusable utility functions |
| `data/` | Runtime data | Created automatically, **backup regularly** |
| `migrations/` | Schema changes | Database migration files |
| `migrations/old/` | Archived | Old migration format (reference only) |

### Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application, routes, middleware |
| `app/database.py` | Database connection, session management |
| `app/models.py` | SQLAlchemy ORM models (database schema) |
| `run_migrations.py` | Database migration runner |
| `run.py` | Quick start script for local development |
| `docker-entrypoint.sh` | Container startup (runs migrations) |
| `requirements.txt` | Python package dependencies |
| `.env` | Environment variables (secrets, config) |
| `.dockerversion` | Version number for Docker tagging |

---

## Security

### Authentication & Authorization

**Password Security**:
- Passwords hashed using **bcrypt** (industry standard)
- Salt automatically generated per password
- Plain-text passwords never stored
- Cost factor: 12 rounds (balanced security/performance)

**Session Management**:
- JWT tokens for authentication
- Tokens stored in HTTP-only cookies (XSS protection)
- Secure flag in production (HTTPS only)
- 30-day token expiration (configurable)
- Token includes user ID and admin status

**Role-Based Access Control**:
- Two roles: **Admin** and **User** (regular)
- Admin-only routes protected via `require_admin` dependency
- User-only routes protected via `require_user` dependency
- First user automatically becomes admin

### Data Security

**SQL Injection Protection**:
- SQLAlchemy ORM (parameterized queries)
- User input never directly interpolated into SQL
- All queries use bound parameters

**Input Validation**:
- Server-side validation for all forms
- Email addresses validated with regex
- Numeric fields validated for type and range
- Required fields enforced

**File System Security**:
- Database file (`data/database.db`) permissions: 644
- Report files permissions: 644
- No user-uploaded files (reduces attack surface)

### Production Security Checklist

Before deploying to production:

- [ ] **Change SECRET_KEY** - Generate secure random key (32+ bytes)
  ```bash
  openssl rand -hex 32
  ```

- [ ] **Use Strong Admin Password** - Minimum 12 characters, mixed case, numbers, symbols

- [ ] **Configure HTTPS/SSL** - Use reverse proxy (nginx/Caddy) with TLS certificates

- [ ] **Set Up Firewall Rules** - Only expose necessary ports
  ```bash
  # Example: UFW firewall (Ubuntu)
  ufw allow 22/tcp    # SSH
  ufw allow 80/tcp    # HTTP (redirect to HTTPS)
  ufw allow 443/tcp   # HTTPS
  ufw deny 5710/tcp   # Block direct access to app
  ufw enable
  ```

- [ ] **Restrict Database Permissions** - Database file should not be world-readable
  ```bash
  chmod 600 data/database.db
  chown appuser:appuser data/database.db
  ```

- [ ] **Secure Resend API Key** - Never commit to git, use environment variables

- [ ] **Never Commit .env** - Already in `.gitignore`, but verify

- [ ] **Set Up Regular Backups** - Automate database backups
  ```bash
  # Example cron job
  0 2 * * * /usr/local/bin/backup-daily-dough.sh
  ```

- [ ] **Configure Monitoring** - Set up application and server monitoring

- [ ] **Review User Access** - Audit admin users regularly

- [ ] **Update Docker Compose** - Use your container registry
  ```yaml
  image: ghcr.io/YOUR_USERNAME/daily-dough:latest
  ```

- [ ] **Verify Email Domain** - Ensure domain is verified in Resend

- [ ] **Enable HTTPS Cookies** - Set `secure=True` for cookies in production

- [ ] **Consider Rate Limiting** - Use reverse proxy for rate limiting

- [ ] **Keep Dependencies Updated** - Regularly update Python packages
  ```bash
  pip list --outdated
  ```

### Generating Secure Keys

```bash
# SECRET_KEY (for JWT signing)
openssl rand -hex 32

# Alternative method
python3 -c "import secrets; print(secrets.token_hex(32))"

# Example output:
# a7f3c8e1d6b4f2a9c5e8d1b7f3a6c9e2d5b8f1a4c7e0d3b6f9a2c5e8d1b4f7a0
```

Add to `.env`:
```env
SECRET_KEY=a7f3c8e1d6b4f2a9c5e8d1b7f3a6c9e2d5b8f1a4c7e0d3b6f9a2c5e8d1b4f7a0
```

### Security Best Practices

1. **Keep Software Updated**
   - Regularly update Python and dependencies
   - Monitor security advisories
   - Apply patches promptly

2. **Use HTTPS in Production**
   - Obtain SSL certificate (Let's Encrypt is free)
   - Configure reverse proxy (nginx/Caddy)
   - Redirect all HTTP to HTTPS

3. **Backup Regularly**
   - Automate daily backups
   - Store backups off-site
   - Test backup restoration

4. **Monitor Logs**
   - Review logs regularly
   - Set up alerts for errors
   - Track authentication failures

5. **Limit Access**
   - Use strong passwords
   - Consider SSH key authentication
   - Disable root login
   - Use VPN for administrative access

6. **Regular Audits**
   - Review user accounts quarterly
   - Check for unused admin accounts
   - Verify email recipient lists

---

## Troubleshooting

### Common Issues

#### Port Already in Use

**Symptoms**: Error message about port 5710 being in use

**Solution (macOS/Linux)**:
```bash
# Find process using port
lsof -i :5710

# Kill process
kill -9 <PID>

# Restart application
python run.py
```

**Solution (Windows)**:
```cmd
# Find process
netstat -ano | findstr :5710

# Kill process (replace <PID>)
taskkill /PID <PID> /F

# Restart application
python run.py
```

#### Missing Dependencies

**Symptoms**: Import errors, module not found

**Solution**:
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install/upgrade dependencies
pip install -r requirements.txt --upgrade

# Verify installation
pip list
```

#### Database Errors

**Symptoms**: Database locked, corruption errors, schema errors

**Solution 1: Backup and Reset**
```bash
# IMPORTANT: Backup first!
cp data/database.db data/database.db.backup

# Reset database
rm data/database.db

# Restart application (creates fresh database)
python run.py
```

**Solution 2: Run Migrations**
```bash
# Run pending migrations
python run_migrations.py

# Check migration status
python -c "
import sqlite3
conn = sqlite3.connect('data/database.db')
for row in conn.execute('SELECT * FROM schema_migrations ORDER BY id'):
    print(row)
"
```

#### Docker Container Won't Start

**Check Logs**:
```bash
docker-compose logs

# Or follow logs
docker-compose logs -f

# Specific service
docker-compose logs app
```

**Common Causes**:
1. Port conflict (5710 already used)
2. Volume mount issues (check permissions)
3. Environment variables missing
4. Database migration failure

**Solution**:
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (if needed)
docker-compose down -v

# Rebuild and start
docker-compose up --build -d

# Check status
docker-compose ps
```

#### Database Issues (Docker)

**Check Data Directory**:
```bash
ls -la ./data
```

**Run Migrations Manually**:
```bash
docker-compose exec app python /app/run_migrations.py
```

**Access Database**:
```bash
docker-compose exec app sqlite3 /app/data/database.db
```

#### Health Check Failing

**Test Manually**:
```bash
curl http://localhost:5710/

# Or
curl -I http://localhost:5710/
```

**Check Container Status**:
```bash
docker ps

# Look for "(unhealthy)" status
```

### Email Issues

#### No Emails Being Sent

**Checklist**:
1. Verify `RESEND_API_KEY` in `.env`
2. Verify from email addresses configured
3. Ensure from addresses verified in Resend
4. Check at least one recipient selected
5. Review application logs for errors

**Check Configuration (Docker)**:
```bash
docker-compose exec app env | grep RESEND
```

**Check Logs**:
```bash
docker-compose logs | grep -i resend
docker-compose logs | grep -i email
```

#### Users Not Receiving Emails

**Checklist**:
1. Verify user has valid email address
2. Check opt-in settings (Admin → Users → Edit)
3. Check spam/junk folder
4. Verify Resend dashboard shows delivery
5. Ensure domain is verified

**Test Email**:
```bash
# From inside container or local Python
python -c "
from app.utils.email import send_daily_balance_email
# Test send...
"
```

### Import Errors (PyCharm)

**Solutions**:

1. **Invalidate Caches**
   - File → Invalidate Caches → Invalidate and Restart

2. **Check Interpreter**
   - File → Settings → Project → Python Interpreter
   - Verify correct virtual environment selected

3. **Mark Source Root**
   - Right-click project folder
   - Mark Directory as → Sources Root

4. **Reinstall Dependencies**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### Permission Errors (Docker)

**Issue**: Cannot write to `data/` directory

**Solution**:
```bash
# Check permissions
ls -la ./data

# Fix permissions (Linux/macOS)
sudo chown -R $(id -u):$(id -g) ./data
chmod -R 755 ./data

# Restart containers
docker-compose restart
```

### Migration Errors

See [Database & Migrations → Troubleshooting Migrations](#troubleshooting-migrations) section above for detailed migration troubleshooting.

---

## Version Management

### Version Numbering

Daily Dough uses **Semantic Versioning** (SemVer):

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)

Example: `1.2.3`
- Major version: 1
- Minor version: 2
- Patch version: 3

### Updating Version

1. **Update `.dockerversion` File**
   ```bash
   echo "1.2.3" > .dockerversion
   ```

2. **Commit and Push**
   ```bash
   git add .dockerversion
   git commit -m "Bump version to 1.2.3"
   git push
   ```

3. **GitHub Actions Automatically**:
   - Builds Docker image
   - Tags with version: `1.2.3`
   - Tags with `latest`
   - Pushes to container registry

### Deploying New Version

```bash
# Pull latest image
docker-compose pull

# Restart with new image
docker-compose up -d

# Verify version
docker-compose exec app cat .dockerversion
```

Migrations run automatically on container restart.

### Version History

See `.dockerversion` for current version.

Major releases:
- **1.0.0** - Initial production release with automated migrations
- **0.0.1** - Initial development version

---

## Support & Resources

### Documentation

- **Application Documentation**: This README
- **Migration Guide**: `migrations/README.md`
- **Quick Start Guide**: `migrations/QUICK_START.md`
- **Migration Examples**: `migrations/example_*.py.example`

### External Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Jinja2 Documentation**: https://jinja.palletsprojects.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Python Documentation**: https://docs.python.org/3/
- **Docker Documentation**: https://docs.docker.com/
- **Resend Documentation**: https://resend.com/docs

### Getting Help

1. **Check Documentation**: Review this README and migration docs
2. **Check Logs**: Application logs often reveal the issue
3. **Search Issues**: Check project issues on GitHub
4. **Create Issue**: Report bugs or request features on GitHub

---

## Command Reference

### Application Management

```bash
# Start application (local)
python run.py

# Start with auto-reload (development)
uvicorn app.main:app --host 0.0.0.0 --port 5710 --reload

# Run migrations
python run_migrations.py
```

### Database Operations

```bash
# Backup database
cp data/database.db data/database.db.backup

# Restore database
cp data/database.db.backup data/database.db

# Reset database (WARNING: deletes all data)
rm data/database.db

# Access database (requires sqlite3)
sqlite3 data/database.db

# Check migration status
sqlite3 data/database.db "SELECT * FROM schema_migrations ORDER BY id;"
```

### Docker Operations

```bash
# === Local Development ===
# Start
docker-compose -f docker-compose.local.yml up -d

# Stop
docker-compose -f docker-compose.local.yml down

# Restart
docker-compose -f docker-compose.local.yml restart

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Rebuild
docker-compose -f docker-compose.local.yml up --build -d

# === Production ===
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Update to latest version
docker-compose pull && docker-compose up -d

# Execute command in container
docker-compose exec app <command>

# Access container shell
docker-compose exec app /bin/bash
```

### Version Management

```bash
# Update version
echo "1.2.3" > .dockerversion

# Commit and push (triggers CI/CD)
git add .dockerversion
git commit -m "Bump version to 1.2.3"
git push

# Pull and deploy new version
docker-compose pull
docker-compose up -d
```

---

## File Locations Quick Reference

| Item | Location |
|------|----------|
| **Database** | `data/database.db` |
| **Daily Balance Reports** | `data/reports/daily_report/{YEAR}/{MONTH}/` |
| **Tip Reports** | `data/reports/tip_report/` |
| **Database Backups** | `data/backups/` |
| **Configuration** | `.env` |
| **Migrations** | `migrations/*.py` |
| **Migration Archive** | `migrations/old/` |
| **Application Logs** | Docker: `docker-compose logs` |
| **Version** | `.dockerversion` |

---

## License

**MIT License**

Copyright (c) 2026 Daily Dough

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

<div align="center">
  <strong>Daily Dough</strong><br>
  Professional daily balance and tip records management for hospitality businesses

  <br><br>

  Made with ❤️ for restaurants and hospitality professionals
</div>
