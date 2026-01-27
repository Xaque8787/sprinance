# Multi-Position & Inactive Status Migration

## What's New

This update adds two major features:

### 1. Multi-Position Support
Employees can now be assigned to **multiple positions**, each with its own schedule:
- Add/remove positions with unique day schedules
- Same employee can work different positions on different days
- Daily balance auto-populates based on employee-position combinations
- Dropdown shows all employee-position combos (e.g., "Smith, John - Server" and "Smith, John - Bartender")

### 2. Inactive Employee Status
Employees can now be marked as inactive:
- Inactive employees **won't auto-populate** in daily balance
- Inactive employees **don't appear** in the "Add Employee" dropdown
- They remain in the system for historical data preservation
- Can still be viewed and edited in the employee list

## Database Changes

The migration automatically:
1. Creates `employee_position_schedule` table for multi-position tracking
2. Adds `is_active` column to employees (defaults to TRUE)
3. Adds `position_id` to daily_employee_entries (tracks which position was worked)
4. Migrates existing data automatically
5. **Preserves all historical data** - nothing is deleted

Old columns (`position_id`, `scheduled_days` in employees table) are kept for rollback safety but are no longer used by the application.

## How to Apply

### For New Installations
No action needed! The database will be created with the new schema automatically.

### For Existing Installations

Run the migration setup script:

```bash
python3 run_migration_setup.py
```

Or manually:

```bash
# If database doesn't exist yet, create it
python3 -c "from app.database import init_db; init_db()"

# Run the migration
python3 migrations/add_multi_position_and_inactive_status.py
```

## What Gets Migrated

For each existing employee:
- Their current `position_id` → becomes one entry in `employee_position_schedule`
- Their `scheduled_days` → copied to that schedule entry
- All existing employees set to `is_active = TRUE`

All existing daily balance entries remain completely untouched.

## How to Use

### Adding Multiple Positions to an Employee

1. Go to Employees → Edit Employee
2. Click "+ Add Position & Schedule"
3. Select position and check scheduled days
4. Add more positions as needed
5. Save

**Validation:**
- At least 1 position required
- Can't assign same position twice
- Days are optional (for manual-add only employees)

### Marking an Employee Inactive

1. Go to Employees → Edit Employee
2. Uncheck "Active" checkbox
3. Save

**Effect:**
- Won't auto-populate in daily balance
- Won't appear in "Add Employee" dropdown
- Still visible in employee list (grayed out)
- Historical data preserved

### Daily Balance Updates

**Auto-Population:**
- System queries `employee_position_schedule` by day of week
- Only includes active employees
- Creates entries for each employee-position combo scheduled for that day

**Manual Add:**
- Dropdown shows all active employee-position combinations
- Grouped by position for easy selection
- Can add same employee multiple times if they have multiple positions

### Position Deletion Protection

Positions can't be deleted if employees are scheduled for them:
- Error message shows count: "Cannot delete Server - 3 employees are scheduled for this position"
- Must remove all schedules first before deleting position

## Rollback (if needed)

If you need to rollback:

1. The old columns still exist in the database
2. You can revert the code changes
3. The application will continue working with the old schema

**Note:** Any new multi-position assignments made after migration will be lost on rollback.

## Testing Checklist

After migration, test:
- [ ] View employee list (shows positions & schedules)
- [ ] Create new employee with multiple positions
- [ ] Edit existing employee to add second position
- [ ] Mark employee as inactive
- [ ] Verify inactive employee doesn't auto-populate
- [ ] Verify inactive employee not in dropdown
- [ ] Open daily balance for a day with schedules
- [ ] Verify correct employee-position combos appear
- [ ] Manually add employee-position combo
- [ ] Save and finalize daily balance
- [ ] Try to delete position with scheduled employees (should fail)

## Questions?

The migration is designed to be safe and preserve all data. If you encounter any issues:
1. Check the migration output for errors
2. Verify the database file exists at `data/database.db`
3. Check that all tables were created properly
