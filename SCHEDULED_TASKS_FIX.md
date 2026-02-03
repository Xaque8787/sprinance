# Scheduled Tasks Bug Fixes

## Issues Fixed

### 1. **Orphaned Task Executions (Root Cause)**
**Problem:** Recent executions were shared across different tasks with the same `task_type`
**Root Cause:** SQLite doesn't enforce foreign key constraints by default
**Solution:** Enabled `PRAGMA foreign_keys=ON` in database.py

**What changed:**
- `app/database.py:30-36` - Added `PRAGMA foreign_keys=ON` to ensure CASCADE deletes work
- When a scheduled_task is deleted, all its task_executions are now automatically deleted via CASCADE
- This prevents orphaned executions from being shown on unrelated tasks

### 2. **Update Task Not Working**
**Problem:** Clicking "Update" sometimes did nothing
**Root Cause:** Silent validation failures with no user feedback
**Solution:** Added comprehensive validation and error handling

**What changed:**
- `app/routes/scheduled_tasks.py:398-544` - Enhanced update endpoint with:
  - Input validation (name, schedule, employee selection)
  - Task existence check before updating
  - Better error messages for validation failures
  - Detailed logging for debugging
- `app/templates/scheduled_tasks/index.html:704-733` - Improved JavaScript error handling
  - Better error messages to user
  - Console logging for debugging
  - Graceful error handling for network failures

### 3. **Explicit Cascade Delete (Safety Measure)**
**Problem:** Even with foreign keys enabled, wanted extra safety
**Solution:** Explicitly delete executions before deleting tasks

**What changed:**
- `app/routes/scheduled_tasks.py:495-527` - Delete endpoint now:
  1. Removes job from APScheduler
  2. Explicitly deletes task_executions
  3. Deletes the scheduled_task
  - This provides defense-in-depth even if foreign keys fail

### 4. **Orphaned Execution Cleanup**
**Problem:** Existing databases may have orphaned executions
**Solution:** Added cleanup function and endpoint

**What changed:**
- `app/routes/scheduled_tasks.py:607-625` - New `cleanup_orphaned_executions()` function
  - Automatically runs on startup when loading scheduled tasks
  - Can be manually triggered via endpoint
- `app/routes/scheduled_tasks.py:658-677` - New POST endpoint `/scheduled-tasks/cleanup-orphaned`
  - Allows admin to manually trigger cleanup
- `app/routes/scheduled_tasks.py:679-736` - Enhanced debug endpoint
  - Shows count of orphaned executions
  - Helps diagnose data integrity issues

## Testing the Fixes

### Verify Foreign Keys Are Enabled
```bash
sqlite3 data/database.db "PRAGMA foreign_keys"
# Should return: 1
```

### Test CASCADE Delete
1. Create a test scheduled task
2. Wait for it to run (or trigger it manually)
3. Verify task_executions exist for that task
4. Delete the scheduled task
5. Verify all its executions are automatically deleted

### Test Update Task
1. Edit an existing task
2. Make changes (name, schedule, etc.)
3. Click "Update Task"
4. Should see success message and page reload
5. Verify changes were saved

### Check for Orphaned Executions
```bash
# Via SQL
sqlite3 data/database.db "SELECT COUNT(*) FROM task_executions WHERE task_id NOT IN (SELECT id FROM scheduled_tasks)"
# Should return: 0

# Via Debug Endpoint
curl http://localhost:8000/scheduled-tasks/debug
# Check "orphaned_executions" field
```

### Cleanup Orphaned Executions (if needed)
```bash
# Run migration script
python3 migrations/2026_02_03_enable_foreign_keys_cleanup.py

# Or use API endpoint
curl -X POST http://localhost:8000/scheduled-tasks/cleanup-orphaned
```

## Migration for Existing Databases

If you have an existing database with orphaned executions, run:

```bash
python3 migrations/2026_02_03_enable_foreign_keys_cleanup.py
```

This will:
1. Enable foreign keys (for that session)
2. Show all orphaned executions
3. Delete them
4. Provide a summary

**Note:** Foreign keys are now automatically enabled on every new database connection via the pragma listener in `database.py`, so this only needs to be run once to clean up existing data.

## Files Modified

1. **app/database.py**
   - Added `PRAGMA foreign_keys=ON` to enable CASCADE deletes

2. **app/routes/scheduled_tasks.py**
   - Enhanced update endpoint with validation and error handling
   - Added explicit cascade delete in delete endpoint
   - Added cleanup_orphaned_executions() function
   - Added cleanup endpoint
   - Enhanced debug endpoint with orphan detection
   - Modified load_scheduled_tasks() to auto-cleanup on startup

3. **app/templates/scheduled_tasks/index.html**
   - Improved JavaScript error handling in handleCreateTask()
   - Better error messages and console logging

4. **migrations/2026_02_03_enable_foreign_keys_cleanup.py**
   - New migration script to clean up existing orphaned data

## Expected Behavior Going Forward

1. **Creating a task**: Works as before
2. **Updating a task**:
   - Shows clear error messages if validation fails
   - Updates successfully with valid data
   - Maintains task execution history
3. **Deleting a task**:
   - Removes task from scheduler
   - Automatically deletes all associated executions
   - No orphaned executions remain
4. **Viewing executions**:
   - Each task shows only ITS OWN executions
   - No cross-contamination between tasks
   - Even tasks with the same task_type have separate execution histories

## Verification Checklist

- [ ] Foreign keys enabled: `PRAGMA foreign_keys` returns 1
- [ ] No orphaned executions: Query returns 0
- [ ] Update task works: Can successfully update task settings
- [ ] Delete cascades: Deleting task removes all executions
- [ ] Separate execution histories: Different tasks don't share executions
- [ ] Error messages visible: Failed updates show helpful error messages
