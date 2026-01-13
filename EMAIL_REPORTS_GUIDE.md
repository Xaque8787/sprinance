# Email Reports Guide

This guide explains how to use the enhanced email reporting system that allows sending formatted HTML emails of reports to multiple recipients.

## Overview

The email system now supports:
- Sending beautifully formatted HTML emails (similar to web UI) instead of CSV attachments
- Multiple recipient selection from admin users
- User opt-in preferences for automatic email delivery
- Additional custom email addresses
- Proper error handling and validation

## Configuration

### Environment Variables

Add these to your `.env` file:

```
RESEND_API_KEY=your_resend_api_key_here
RESEND_FROM_EMAIL_DAILY=daily@yourdomain.com
RESEND_FROM_EMAIL_TIPS=tips@yourdomain.com
```

**Important:**
- Replace `yourdomain.com` with your verified domain in Resend
- All three variables must be configured for email functionality to work
- The from email addresses must be verified in your Resend account

### Docker Configuration

The `docker-compose.yml` has been updated to include these environment variables. They can be:
1. Set in a `.env` file next to your `docker-compose.yml`
2. Or defined directly in the compose file

## User Opt-In Settings

### Setting Up Opt-In Preferences

1. Navigate to Admin > Users
2. Edit any user
3. Under "Email Report Preferences":
   - Check "Automatically receive Daily Balance Reports" for daily report opt-in
   - Check "Automatically receive Tip Reports" for tip report opt-in

**Note:** Users must have an email address configured to receive reports.

### How Opt-In Works

When generating a report:
- Users who have opted in will be pre-selected in the email modal
- This requires no manual action - reports are automatically sent to opted-in users
- Users can still be manually deselected if needed

## Using the Email System

### From the UI

1. Navigate to any report page (Daily Balance or Tip Reports)
2. Click "Email" button on a saved report or "Send via Email" when generating a new report
3. In the email modal:
   - Admin users with emails will be listed with checkboxes
   - Users who have opted in will be pre-checked
   - Optionally check "Additional Email" to add a custom email address
   - Click "Send Email"

### Email Modal Features

#### Admin User Selection
- All admin users with email addresses are displayed
- Users who have opted in for that report type are pre-checked
- Simply check/uncheck users as needed

#### Additional Email
- Check "Additional Email" checkbox to reveal email input field
- Enter any valid email address
- Email format is validated before sending

#### Error Handling
- If no recipients are selected, an error message is shown
- Invalid email addresses are rejected
- Failed sends are reported with specific error messages

## Report Email Format

Emails are sent as beautifully formatted HTML that matches the web UI:

### Daily Balance Reports Include:
- Report period
- Daily summaries with revenue, expenses, and cash over/under
- Revenue & income breakdown
- Deposits & expenses breakdown
- Employee tip breakdown for each day

### Tip Reports Include:
- Report period
- Employee summary table with totals
- Daily breakdown per employee
- All tip calculations and adjustments

**No CSV attachments** - everything is inline HTML for easy reading.

## API Endpoints

The following endpoints have been added:

### Get Admin Users for Email
```
GET /reports/api/admin-users?report_type=daily|tips
```
Returns list of admin users with emails and their opt-in status.

### Send Daily Balance Email
```
POST /reports/daily-balance/email
POST /reports/daily-balance/email/{year}/{month}/{filename}
```

### Send Tip Report Email
```
POST /reports/tip-report/email
POST /reports/tip-report/email/{filename}
POST /reports/tip-report/employee/{employee_slug}/email
```

All endpoints accept:
- `user_emails[]` - Array of selected user emails
- `additional_email` - Optional additional email address
- Date parameters (for generated reports)

## Database Changes

### New User Fields
- `opt_in_daily_reports` (Boolean) - Default: False
- `opt_in_tip_reports` (Boolean) - Default: False

### Migration
The migration `add_user_email_opt_in.py` adds these fields automatically when the application starts or when manually run.

## Troubleshooting

### No Emails Being Sent
1. Check that `RESEND_API_KEY` is set correctly in your `.env` file
2. Verify `RESEND_FROM_EMAIL_DAILY` and `RESEND_FROM_EMAIL_TIPS` are configured
3. Ensure the from email addresses are verified in your Resend account
4. Check that at least one recipient is selected
5. For Docker deployments, verify the environment variables are passed through in `docker-compose.yml`

### Users Not Receiving Emails
1. Verify user has a valid email address in their profile
2. Check opt-in settings if expecting automatic delivery
3. Verify Resend API key has permission to send from the configured domains

### Email Validation Errors
- Ensure email addresses follow standard format: `user@domain.com`
- Check for typos in the additional email field

## Future Enhancements

Potential improvements:
- Email templates customization
- Scheduled email delivery
- Email delivery history
- Bulk email management

## Security Notes

- Email addresses are validated server-side
- Only authenticated admin users can send reports
- Resend API key should be kept secure and not committed to version control
- Email sending is rate-limited by Resend's API

## Support

For issues or questions:
1. Check the console for detailed error messages
2. Verify environment variables are correctly set
3. Review the Resend dashboard for delivery status
4. Check application logs for detailed error information
