"""
Migration: Reorganize Tip Report Files into Year/Month Structure

Date: 2026-02-06
Description:
    Moves all existing tip report CSV files from the flat directory structure
    (data/reports/tip_report/) to a hierarchical year/month structure
    (data/reports/tip_report/{year}/{month}/).

    For reports spanning multiple months, the file is placed in the directory
    corresponding to the starting month of the date range.
"""

import os
import shutil
import re
from datetime import datetime

def run_migration():
    """
    Reorganize tip report files into year/month directory structure.
    """
    print("=" * 80)
    print("MIGRATION: Reorganize Tip Report Files")
    print("=" * 80)

    reports_base_dir = "data/reports/tip_report"

    if not os.path.exists(reports_base_dir):
        print(f"✗ Reports directory not found: {reports_base_dir}")
        return False

    # Get all CSV files in the base directory (not in subdirectories)
    csv_files = [
        f for f in os.listdir(reports_base_dir)
        if f.endswith('.csv') and os.path.isfile(os.path.join(reports_base_dir, f))
    ]

    if not csv_files:
        print("ℹ No files to migrate (all files are already organized)")
        return True

    print(f"\nFound {len(csv_files)} file(s) to migrate\n")

    moved_count = 0
    error_count = 0

    for filename in csv_files:
        try:
            # Extract date from filename
            # Format: tip-report-{start_date}-to-{end_date}.csv
            # or: tip-report-{employee_slug}-{start_date}-to-{end_date}.csv
            match = re.search(r'(\d{4}-\d{2}-\d{2})-to-(\d{4}-\d{2}-\d{2})', filename)

            if not match:
                print(f"⚠ Skipping {filename}: Unable to parse date range")
                error_count += 1
                continue

            start_date_str = match.group(1)

            # Parse the start date to get year and month
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            year = str(start_date.year)
            month = f"{start_date.month:02d}"

            # Create destination directory structure
            dest_dir = os.path.join(reports_base_dir, year, month)
            os.makedirs(dest_dir, exist_ok=True)

            # Move the file
            src_path = os.path.join(reports_base_dir, filename)
            dest_path = os.path.join(dest_dir, filename)

            # Check if destination file already exists
            if os.path.exists(dest_path):
                print(f"⚠ Skipping {filename}: File already exists at destination")
                continue

            shutil.move(src_path, dest_path)
            print(f"✓ Moved: {filename} → {year}/{month}/")
            moved_count += 1

        except Exception as e:
            print(f"✗ Error moving {filename}: {str(e)}")
            error_count += 1

    print("\n" + "=" * 80)
    print(f"Migration Complete:")
    print(f"  • Files moved: {moved_count}")
    print(f"  • Errors: {error_count}")
    print("=" * 80)

    return error_count == 0

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
