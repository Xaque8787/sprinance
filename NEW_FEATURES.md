# New Features - Daily Balance CRUD System

## Overview
The Daily Balance page has been significantly enhanced with new features for better flexibility and real-time calculations.

## Key Features

### 1. Real-Time Take-Home Tips Calculation
- **What it does**: The "Take-Home Tips" field now calculates automatically as you type
- **How it works**: Enter values in Bank Card Tips, Cash Tips, Adjustments, and Tips on Paycheck fields
- **Formula**: `Take-Home Tips = Bank Card Tips + Cash Tips + Adjustments - Tips on Paycheck`
- **Benefit**: No need to save draft to see the calculated value

### 2. Tips on Paycheck Field
- **New field**: Added to Employee Entries section
- **Purpose**: Track tips that will be paid through payroll instead of cash
- **Behavior**:
  - Subtracts from Take-Home Tips
  - Automatically appears in Revenue & Income section when value is greater than zero
  - Shows as "[Employee Name] - Tips on Paycheck" in the financial summary
- **Use case**: When an employee requests tips to be added to their paycheck for tax/record purposes

### 3. CRUD Financial Line Items
The Revenue & Income and Deposits & Expenses tables are now fully manageable.

#### What Changed:
- **Before**: Hardcoded list of financial categories
- **After**: Dynamic system with persistent templates

#### Features:
- **Default Templates**: The system comes with all previous categories as default templates
- **Persistence**: Templates persist across all days
- **Day-Specific Values**: Each day stores its own values for each template
- **Employee Tips Integration**: Tips on Paycheck entries are automatically added to Revenue & Income for the specific day

#### Current Default Templates:

**Revenue & Income:**
- Cash Drawers Beginning
- Food Sales
- Non Alcohol Beverage Sales
- Beer Sales
- Wine Sales
- Other Revenue
- Catering Sales
- Fundraising Contributions
- Sales Tax Payable
- Gift Certificate Sold

**Deposits & Expenses:**
- Gift Certificate Redeemed
- Checking Account Cash Deposit
- Checking Account Bank Cards
- Cash Paid Out
- Cash Drawers End

## Migration

### For New Installations:
No migration needed. The system will automatically create the correct database structure on first run.

### For Existing Installations:
Run the migration script to transition to the new system:

```bash
python3 migrate_to_crud_system.py
```

This migration will:
1. Create new tables for CRUD financial items
2. Add the tips_on_paycheck column
3. Migrate all existing financial data to the new structure
4. Remove old hardcoded columns
5. Set up default templates

**Important**: Back up your database before running the migration!

```bash
cp data/database.db data/database.db.backup
```

## CSV Reports

CSV reports have been updated to include:
- Complete financial summary with all line items
- Revenue & Income breakdown
- Deposits & Expenses breakdown
- Cash Over/Under calculation
- Tips on Paycheck column in employee breakdown

## Usage Tips

### Daily Balance Entry:
1. Select the date
2. Enter financial line item values (automatically saved with templates)
3. Add employees working that day
4. For each employee, enter:
   - Bank Card Sales
   - Bank Card Tips
   - Total Sales
   - Cash Tips
   - Adjustments (if any)
   - Tips on Paycheck (if applicable)
5. Watch Take-Home Tips calculate in real-time
6. Save Draft or Generate Report

### Tips on Paycheck Workflow:
1. Employee requests $50 in tips on their paycheck
2. Enter 50.00 in the "Tips on Paycheck" field for that employee
3. The system automatically:
   - Subtracts $50 from their Take-Home Tips
   - Adds "$50.00 - [Employee Name] - Tips on Paycheck" to Revenue & Income
   - Includes this in the Cash Over/Under calculation
4. When you Generate Report, this appears in the CSV for accounting records

## Future Enhancements

Potential additions for managing templates:
- Admin interface to add custom financial line items
- Ability to remove or hide default templates
- Reorder line items
- Archive unused templates

These features can be added through the existing API endpoints in `/api/financial-items/templates`.
