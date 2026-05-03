import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ALLOWED_USERS = [int(u.strip()) for u in os.getenv("TELEGRAM_ALLOWED_USERS", "7714508470").split(",") if u.strip()]
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "password")
COMMAND_LOG_PATH = os.path.expanduser("~/openclaw_commands.log")

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

def set_lock(locked):
    global is_locked
    is_locked = locked

def get_lock():
    return is_locked
