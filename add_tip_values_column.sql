-- Add tip_values column to daily_employee_entries table
-- This column stores dynamic tip requirement values as JSON

ALTER TABLE daily_employee_entries
ADD COLUMN tip_values TEXT DEFAULT '{}';
