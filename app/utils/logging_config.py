import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

LOG_DIR = Path("data/logs")
LOG_FILE = LOG_DIR / "error_log.txt"

_file_handler = None


class NoiseFilter(logging.Filter):
    """Filter out noisy third-party library debug logs."""

    NOISY_LOGGERS = [
        'multipart.multipart',
        'asyncio',
        'watchfiles',
    ]

    def filter(self, record):
        for noisy in self.NOISY_LOGGERS:
            if record.name.startswith(noisy) and record.levelno == logging.DEBUG:
                return False
        return True


class SuppressRootRedirectFilter(logging.Filter):
    """Suppress the noisy '/ -> 302' redirect logs from health checks."""

    def filter(self, record):
        # Only filter uvicorn access logs
        if record.name != "uvicorn.access":
            return True

        message = record.getMessage()
        # Suppress only "GET / HTTP/1.1" with 302 response
        return not ('"GET / HTTP/1.1" 302' in message)

def setup_error_logging(max_bytes=10485760, backup_count=5, log_level=logging.ERROR):
    """
    Configure rotating file handler and console handler for error logging.

    Args:
        max_bytes: Maximum size of log file before rotation (default 10MB)
        backup_count: Number of backup files to keep (default 5)
        log_level: Minimum log level to capture (default ERROR)
    """
    global _file_handler

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler for web UI
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.addFilter(NoiseFilter())
    file_handler.setFormatter(formatter)

    # Console handler for Docker logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.addFilter(NoiseFilter())
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    if root_logger.level > log_level:
        root_logger.setLevel(log_level)

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.addHandler(file_handler)
    uvicorn_access.addHandler(console_handler)
    uvicorn_access.addFilter(SuppressRootRedirectFilter())
    uvicorn_access.setLevel(log_level)

    _file_handler = file_handler
    return file_handler


def get_log_files():
    """Get all log files (main and rotated)."""
    if not LOG_DIR.exists():
        return []

    log_files = []
    if LOG_FILE.exists():
        log_files.append(LOG_FILE)

    for i in range(1, 100):
        rotated_file = Path(f"{LOG_FILE}.{i}")
        if rotated_file.exists():
            log_files.append(rotated_file)
        else:
            break

    return log_files


def read_log_file(file_path, max_lines=1000):
    """
    Read log file and return lines in reverse order (newest first).

    Args:
        file_path: Path to log file
        max_lines: Maximum number of lines to return

    Returns:
        List of log lines (newest first)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-max_lines:][::-1]
    except Exception as e:
        logging.error(f"Error reading log file {file_path}: {e}")
        return []


def get_log_stats():
    """Get statistics about log files."""
    log_files = get_log_files()

    total_size = 0
    file_info = []

    for log_file in log_files:
        size = log_file.stat().st_size
        total_size += size
        file_info.append({
            'name': log_file.name,
            'path': str(log_file),
            'size': size,
            'size_mb': round(size / (1024 * 1024), 2)
        })

    return {
        'total_files': len(log_files),
        'total_size': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'files': file_info
    }


def clear_log_file():
    """
    Clear the current log file by truncating it.
    This preserves the file but removes all content.
    """
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                f.truncate(0)
            logging.info("Log file cleared by administrator")
            return True
        return False
    except Exception as e:
        logging.error(f"Error clearing log file: {e}")
        return False


def reconfigure_logging():
    """
    Reconfigure logging based on current database settings.
    Called when log level settings are updated.
    """
    global _file_handler

    try:
        from app.database import SessionLocal
        from app.models import Setting

        db = SessionLocal()
        try:
            log_capture_info = db.query(Setting).filter(Setting.key == "log_capture_info").first()
            log_capture_debug = db.query(Setting).filter(Setting.key == "log_capture_debug").first()

            capture_info = log_capture_info and log_capture_info.value == "1"
            capture_debug = log_capture_debug and log_capture_debug.value == "1"

            if capture_debug:
                new_level = logging.DEBUG
            elif capture_info:
                new_level = logging.INFO
            else:
                new_level = logging.WARNING

            # Update all handlers on root logger
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                handler.setLevel(new_level)

            if root_logger.level > new_level:
                root_logger.setLevel(new_level)

            # Update uvicorn access logger
            uvicorn_access = logging.getLogger("uvicorn.access")
            # Ensure the suppress filter is always present
            if not any(isinstance(f, SuppressRootRedirectFilter) for f in uvicorn_access.filters):
                uvicorn_access.addFilter(SuppressRootRedirectFilter())

            for handler in uvicorn_access.handlers:
                handler.setLevel(new_level)
            uvicorn_access.setLevel(new_level)

            logging.info(f"Logging reconfigured to level: {logging.getLevelName(new_level)}")

        finally:
            db.close()

    except Exception as e:
        logging.error(f"Error reconfiguring logging: {e}")
