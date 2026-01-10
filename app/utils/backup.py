import os
import shutil
from datetime import datetime
from typing import List, Dict
import sqlite3


def create_backup() -> str:
    backups_dir = "data/backups"
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.db"
    filepath = os.path.join(backups_dir, filename)

    db_path = "data/tips.db"

    if not os.path.exists(db_path):
        raise FileNotFoundError("Database file not found")

    src_conn = sqlite3.connect(db_path)
    dst_conn = sqlite3.connect(filepath)

    src_conn.backup(dst_conn)

    src_conn.close()
    dst_conn.close()

    return filename


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

    return backups[:7]


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
