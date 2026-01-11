# Quick Start Guide

Get up and running in 5 minutes.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Start the Server

```bash
python run.py
```

Or:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5710 --reload
```

## 3. Open Browser

Navigate to: http://localhost:5710

## 4. Create Admin Account

On first run, you'll see the setup page:
1. Enter admin username
2. Enter admin password
3. Click "Create Admin Account"

## 5. Start Using

You're now logged in and can:
- Manage employees at `/employees`
- Track daily balance at `/daily-balance`
- Manage users at `/admin` (admin only)

## Common Commands

### Run in development mode with auto-reload:
```bash
python run.py
```

### Reset database (delete all data):
```bash
rm data/database.db
python run.py
```

### Check what's using port 5710:
```bash
# macOS/Linux
lsof -i :5710

# Windows
netstat -ano | findstr :5710
```

## Default Port

The application runs on **port 5710** by default.

## File Locations

- **Database:** `data/database.db`
- **Reports:** `data/reports/daily_report/{YEAR}/{MONTH}/YYYY-MM-DD-daily-balance.csv`
- **Configuration:** `app/auth/jwt_handler.py` (SECRET_KEY)

## Need More Help?

See:
- `README.md` - Full documentation
- `INSTALLATION.md` - Detailed PyCharm setup guide
