# Setup Guide for New Features

## Quick Start

### If you have an existing database:

1. **Backup your database first!**
   ```bash
   cp data/database.db data/database.db.backup
   ```

2. **Run the migration script:**
   ```bash
   python3 migrate_to_crud_system.py
   ```

3. **Start the application:**
   ```bash
   python3 run.py
   ```

### If you're starting fresh:

1. **Delete the old database (if it exists):**
   ```bash
   rm -f data/database.db
   ```

2. **Start the application:**
   ```bash
   python3 run.py
   ```

   The system will automatically create the correct database structure with all the new features.

## What's New

See [NEW_FEATURES.md](NEW_FEATURES.md) for a complete overview of all new functionality.

### Key Changes:
✅ Real-time calculation of Take-Home Tips
✅ New "Tips on Paycheck" field that integrates with revenue tracking
✅ CRUD system for financial line items (Revenue & Income, Deposits & Expenses)
✅ Dynamic employee tips automatically added to financial summary
✅ Updated CSV reports with complete financial breakdown

## Testing the Features

1. **Go to Daily Balance page**
2. **Test Real-Time Calculation:**
   - Add an employee
   - Enter Bank Card Tips: 100
   - Enter Cash Tips: 50
   - Watch Take-Home Tips automatically show 150.00

3. **Test Tips on Paycheck:**
   - Enter Tips on Paycheck: 30
   - Watch Take-Home Tips change to 120.00
   - Look at Revenue & Income table - you'll see the employee's tips added there

4. **Test Financial Tables:**
   - All your previous financial categories are still there
   - Enter values as before
   - Everything persists across days

5. **Generate a Report:**
   - Click "Generate Report (Finalize)"
   - Download the CSV
   - Check that it includes the financial summary and Tips on Paycheck column

## Troubleshooting

### Migration errors:
- Make sure you backed up your database
- Check that Python 3 is installed: `python3 --version`
- Check database file permissions
- Review migration output for specific errors

### Application won't start:
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify the data directory exists: `mkdir -p data/backups data/reports`
- Check the console output for error messages

### Data looks wrong:
- Restore from backup: `cp data/database.db.backup data/database.db`
- Re-run migration if needed
- Contact support with specific issues

## Notes

- The old hardcoded columns have been removed from the database
- All existing data has been migrated to the new CRUD structure
- Financial templates are shared across all days
- Each day stores its own values for each template
- Employee tips on paycheck are day-specific and automatically managed
