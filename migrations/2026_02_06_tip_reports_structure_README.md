# Tip Reports Directory Structure Migration

## Overview

This migration reorganizes tip report CSV files from a flat directory structure into a hierarchical year/month structure, matching the approach used for daily balance reports.

## Changes

### Before
```
data/reports/tip_report/
├── tip-report-2026-01-01-to-2026-01-31.csv
├── tip-report-vanchiere-zachary-2026-01-01-to-2026-01-31.csv
└── tip-report-2026-02-01-to-2026-02-14.csv
```

### After
```
data/reports/tip_report/
├── 2026/
│   ├── 01/
│   │   ├── tip-report-2026-01-01-to-2026-01-31.csv
│   │   └── tip-report-vanchiere-zachary-2026-01-01-to-2026-01-31.csv
│   └── 02/
│       └── tip-report-2026-02-01-to-2026-02-14.csv
```

## Directory Placement Rules

- **All tip reports** (both general and employee-specific) follow the same structure
- Reports are placed in directories based on the **start date** of the report
- For reports spanning multiple months, the file goes in the **first month's folder**
  - Example: A report from `2026-01-28` to `2026-02-14` goes in `2026/01/`

## Files Modified

### Backend Code
1. **`app/utils/csv_generator.py`**
   - Updated `generate_tip_report_csv()` to create year/month directories
   - Updated `generate_employee_tip_report_csv()` to create year/month directories

2. **`app/services/scheduler_tasks.py`**
   - Updated `run_tip_report_task()` to use new file paths
   - Updated `run_employee_tip_report_task()` to use new file paths

3. **`app/routes/reports.py`**
   - Updated all tip report routes to include year/month in URL paths
   - Changed routes from `/reports/tip-report/view/{filename}` to `/reports/tip-report/view/{year}/{month}/{filename}`
   - Updated file path construction throughout

4. **`app/utils/csv_reader.py`**
   - Updated `get_saved_tip_reports()` to scan year/month subdirectories
   - Now returns `year` and `month` fields in report metadata

### Frontend Templates
1. **`app/templates/reports/saved_tip_reports.html`**
   - Updated links to include year/month parameters

2. **`app/templates/reports/tip_report_list.html`**
   - Updated report card links to include year/month parameters

3. **`app/templates/reports/view_saved_tip_report.html`**
   - Updated download link to include year/month parameters

## Migration Script

The migration script `2026_02_06_reorganize_tip_reports.py`:
- Scans the base `data/reports/tip_report/` directory for CSV files
- Extracts the start date from each filename
- Creates the appropriate `{year}/{month}/` subdirectory
- Moves files to their new locations
- Provides detailed logging of the migration process

### Running the Migration

```bash
python3 migrations/2026_02_06_reorganize_tip_reports.py
```

The script is idempotent and can be run multiple times safely.

## Benefits

1. **Consistency**: Tip reports now follow the same structure as daily balance reports
2. **Organization**: Easier to find reports by date
3. **Performance**: Reduced directory listing overhead for large numbers of reports
4. **Maintainability**: Single pattern for all report types

## Backwards Compatibility

After this migration, old URLs pointing to flat file paths will no longer work. The migration script must be run to move existing files to the new structure before deploying the code changes.

## Testing

To test the migration:
1. Create sample tip report files in the old flat structure
2. Run the migration script
3. Verify files are moved to year/month subdirectories
4. Test viewing, downloading, and emailing reports through the UI
