import os
import httpx
from typing import Optional, Tuple

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/Xaque8787/dailydough/refs/heads/main/.dockerversion"
VERSION_FILE_PATH = ".dockerversion"

def get_local_version() -> str:
    try:
        if os.path.exists(VERSION_FILE_PATH):
            with open(VERSION_FILE_PATH, 'r') as f:
                return f.read().strip()
    except Exception:
        pass
    return "unknown"

def get_remote_version() -> Optional[str]:
    try:
        response = httpx.get(GITHUB_VERSION_URL, timeout=5.0)
        if response.status_code == 200:
            return response.text.strip()
    except Exception:
        pass
    return None

def check_version() -> Tuple[str, bool]:
    local_version = get_local_version()
    remote_version = get_remote_version()

    update_available = False
    if remote_version and remote_version != local_version:
        update_available = True

    return local_version, update_available
