import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3
from app.database import DATABASE_PATH


def get_backup_retention_count() -> int:
    """Get the backup retention count from settings."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'backup_retention_count'")
        result = cursor.fetchone()
        conn.close()

        if result:
            return int(result[0])
        return 7
    except Exception:
        return 7


def cleanup_old_backups(retention_count: Optional[int] = None) -> int:
    """
    Remove old backups beyond the retention count.
    Returns the number of backups deleted.
    """
    if retention_count is None:
        retention_count = get_backup_retention_count()

    backups_dir = "data/backups"
    if not os.path.exists(backups_dir):
        return 0

    backups = []
    for filename in os.listdir(backups_dir):
        if filename.endswith('.db'):
            filepath = os.path.join(backups_dir, filename)
            stat = os.stat(filepath)
            backups.append({
                'filename': filename,
                'filepath': filepath,
                'created_at': datetime.fromtimestamp(stat.st_mtime)
            })

    backups.sort(key=lambda x: x['created_at'], reverse=True)

    deleted_count = 0
    if len(backups) > retention_count:
        for backup in backups[retention_count:]:
            try:
                os.remove(backup['filepath'])
                deleted_count += 1
            except Exception:
                pass

    return deleted_count


def create_backup() -> str:
    backups_dir = "data/backups"
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)

    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError("Database file not found")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.db"
    filepath = os.path.join(backups_dir, filename)

    src_conn = None
    dst_conn = None

    try:
        src_conn = sqlite3.connect(DATABASE_PATH)
        dst_conn = sqlite3.connect(filepath)

        with src_conn:
            src_conn.backup(dst_conn)

        dst_conn.close()
        src_conn.close()

        if not os.path.exists(filepath):
            raise Exception("Backup file was not created")

        if os.path.getsize(filepath) == 0:
            os.remove(filepath)
            raise Exception("Backup file is empty")

        cleanup_old_backups()

        return filename

    except Exception as e:
        if dst_conn:
            dst_conn.close()
        if src_conn:
            src_conn.close()

        if os.path.exists(filepath):
            os.remove(filepath)

        raise Exception(f"Backup failed: {str(e)}")


def list_backups() -> List[Dict[str, any]]:
    backups_dir = "data/backups"

    if not os.path.exists(backups_dir):
        return []

    backups = []
    for filename in os.listdir(backups_dir):
        if filename.endswith('.db'):
            filepath = os.path.join(backups_dir, filename)
            stat = os.stat(filepath)
            backups.append({
                'filename': filename,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_mtime)
            })

    backups.sort(key=lambda x: x['created_at'], reverse=True)

    return backups


def delete_backup(filename: str) -> bool:
    backups_dir = "data/backups"
    filepath = os.path.join(backups_dir, filename)

    if not filename.endswith('.db'):
        return False

    if '..' in filename or '/' in filename:
        return False

    if os.path.exists(filepath):
        os.remove(filepath)
        return True

    return False


def get_backup_path(filename: str) -> str:
    backups_dir = "data/backups"

    if not filename.endswith('.db'):
        raise ValueError("Invalid filename")

    if '..' in filename or '/' in filename:
        raise ValueError("Invalid filename")

    filepath = os.path.join(backups_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError("Backup file not found")

    return filepath


def restore_backup(filename: str) -> bool:
    """
    Restore database from a backup file.
    This function will:
    1. Validate the backup file exists
    2. Copy the backup file to the database location

    Important: All database connections must be closed before calling this function.
    """
    backups_dir = "data/backups"
    backup_filepath = os.path.join(backups_dir, filename)

    if not filename.endswith('.db'):
        raise ValueError("Invalid filename")

    if '..' in filename or '/' in filename:
        raise ValueError("Invalid filename")

    if not os.path.exists(backup_filepath):
        raise FileNotFoundError("Backup file not found")

    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError("Current database file not found")

    try:
        conn = sqlite3.connect(backup_filepath)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

        if not tables:
            raise ValueError("Backup file appears to be empty or corrupted")

        shutil.copy2(backup_filepath, DATABASE_PATH)

        return True

    except sqlite3.Error as e:
        raise ValueError(f"Backup file is not a valid SQLite database: {str(e)}")
    except Exception as e:
        raise Exception(f"Restore failed: {str(e)}")
