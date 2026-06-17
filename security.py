import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Strict Environment Loading
ALLOWED_USERS_RAW = os.getenv("TELEGRAM_ALLOWED_USERS", "")
ALLOWED_USERS = [int(u.strip()) for u in ALLOWED_USERS_RAW.split(",") if u.strip()]

def get_admin_id():
    """Return the first user in the allowed list as the primary admin."""
    return ALLOWED_USERS[0] if ALLOWED_USERS else None
# Place command log in project root (one level above this module)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMMAND_LOG_PATH = os.path.join(PROJECT_ROOT, "openclaw_commands.log")

# State for locking
is_locked = False

def check_user(user_id):
    return user_id in ALLOWED_USERS

def log_command(user_id, command_type, command, status, error=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{user_id}] [{command_type}] {command} - {status}"
    if error:
        log_entry += f" - Error: {error}"
    
    try:
        with open(COMMAND_LOG_PATH, "a") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Failed to log command: {e}")

#need to clean up this later

def set_lock(locked):
    global is_locked
    is_locked = locked

def get_lock():
    return is_locked
