import os
import re
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load env vars
load_dotenv()

# Project Root Resolution
# Concept: Path object resolution. We resolve Path(__file__).parent to find the root folder
# of the project regardless of which directory the command is run from.
PROJECT_ROOT = Path(__file__).parent.resolve()

# Absolute paths — Local first for portability
LOCAL_WORKSPACE = PROJECT_ROOT / "workspace"

# We removed GLOBAL_WORKSPACE as it was dead/unused code.
# MEMORY_DIR points to the local workspace folder.
MEMORY_DIR = LOCAL_WORKSPACE
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_FILE = MEMORY_DIR / "MEMORY.md"
DAILY_LOG_DIR = MEMORY_DIR / "memory"
DAILY_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Concurrency Guard Lock
# Concept: asyncio.Lock. 
# Why it exists: Since extract_and_save_facts is called asynchronously via asyncio.create_task,
# multiple instances can run concurrently. Because this function performs a read-modify-write operation
# on MEMORY_FILE, two tasks running in parallel could read the same initial state, query the API, 
# and write back, leading to one task overwriting the facts written by the other (a classic race condition).
# This lock ensures only one task executes the read-extract-write transaction at any given time.
_memory_lock = asyncio.Lock()

def get_daily_log_path() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return str(DAILY_LOG_DIR / f"{today}.md")

def ensure_memory_exists():
    if not MEMORY_FILE.exists():
        with open(MEMORY_FILE, "w") as f:
            f.write("# MEMORY.md — Long-Term Persistent Memory\nLast updated: " + datetime.now().strftime("%Y-%m-%d") + "\n\n***\n")
        print(f"[MEMORY] Created fresh {MEMORY_FILE}")

async def extract_and_save_facts(user_message: str, bot_response: str, groq_client, current_model: str):
    """
    Use AI to extract clean facts from conversation and update MEMORY.md.
    Strict date segregation: ## Session Notes — YYYY-MM-DD
    """
    # Concept: Async Context Manager (async with)
    # Why it exists: Acquires the global lock for the duration of the fact extraction block.
    # What it solves: Serialization of asynchronous file operations to prevent data overwrites.
    async with _memory_lock:
        ensure_memory_exists()
        
        # Read current MEMORY.md
        # Concept: Explicit Exception Handling
        # Why it exists: We replaced the silent "except: pass" block with explicit type checks.
        # What it solves: Prevents silent failures of crucial workspace file reading. If the file
        # is missing (FileNotFoundError), we default to empty text. Other errors (like PermissionsError)
        # are explicitly printed so developers can see the failure.
        current_memory = ""
        try:
            with open(MEMORY_FILE, 'r') as f:
                current_memory = f.read()
        except FileNotFoundError:
            current_memory = ""
        except Exception as e:
            print(f"[MEMORY READ ERROR] Failed to read {MEMORY_FILE}: {e}")
        
        # Use Groq to extract facts
        extraction_prompt = f"""You are a high-precision memory system for OpenClaw. 
Your goal is to extract important facts from the conversation to be stored in MEMORY.md.

CURRENT MEMORY:
{current_memory[-2000:]}

NEW CONVERSATION:
User: {user_message}
Bot: {bot_response[:1000]}

TASK: 
1. Identify any NEW facts: User preferences, project updates, technical decisions, or personal details.
2. If no NEW facts exist, respond EXACTLY with: NO_NEW_FACTS
3. If new facts exist, format them as clean, professional bullet points.
4. DO NOT repeat information already in CURRENT MEMORY.
5. Extract the MEANING, not the raw words.

Formatting Examples:
- Praveen prefers using Groq for all LLM tasks due to speed.
- AutoGen Studio v0.4.2.2 installed at ~/.local/lib/python3.12/site-packages
- User's dog is a Pug named Baddu.

Respond with ONLY the bullet points:"""

        try:
            target_model = current_model if current_model else os.getenv("PRIMARY_MODEL", "llama-3.3-70b-versatile")
            
            # Concept: Thread Pool Executor Delegation (run_in_executor)
            # Why it exists: Calling the synchronous completions.create client blocks the asyncio event loop.
            # What it solves: Spawns the blocking HTTP network call in a separate thread so the main
            # asyncio event loop can keep running other concurrent tasks (like telegram polling).
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: groq_client.chat.completions.create(
                    model=target_model,
                    messages=[{"role": "user", "content": extraction_prompt}],
                    max_tokens=300,
                    temperature=0.1
                )
            )
            
            extracted = response.choices[0].message.content.strip()
            
            upper_ext = extracted.upper()
            if "NO_NEW_FACTS" in upper_ext or "NO NEW FACTS" in upper_ext or extracted == "SKIP" or not extracted:
                return
            
            # Clean up extracted bullets
            lines = []
            for line in extracted.split('\n'):
                line = line.strip()
                if not line: continue
                line = re.sub(r'^[-*•\d.]+\s*', '', line).strip()
                if line and len(line) > 10: 
                    lower_line = line.lower()
                    if "no new facts" in lower_line or "nothing new" in lower_line or "conversation only" in lower_line:
                        continue
                    lines.append(f"- {line}")
                
            if not lines:
                return

            with open(MEMORY_FILE, 'r') as f:
                content = f.read()
                
            today = datetime.now().strftime("%Y-%m-%d")
            new_bullets = "\n".join(lines)
            
            if new_bullets in content:
                return

            # Update Last updated date
            content = re.sub(r"Last updated: \d{4}-\d{2}-\d{2}", f"Last updated: {today}", content)

            # Logic for Session Notes — YYYY-MM-DD
            # Concept: Markdown Splitting & Manipulation. We isolate the daily section
            # and append facts under the current day's header.
            header_today = f"## Session Notes — {today}"
            
            if header_today in content:
                # Section exists, append to it
                parts = content.split(header_today)
                rest = parts[1].strip()
                if "\n## " in rest:
                    sub_parts = rest.split("\n## ", 1)
                    content = parts[0] + header_today + "\n" + sub_parts[0].strip() + "\n" + new_bullets + "\n\n## " + sub_parts[1]
                else:
                    content = parts[0] + header_today + "\n" + rest + "\n" + new_bullets + "\n"
            else:
                # Section missing, create it at the bottom
                content = content.strip() + f"\n\n{header_today}\n{new_bullets}\n"
            
            with open(MEMORY_FILE, 'w') as f:
                f.write(content.strip() + "\n")
                
        except Exception as e:
            print(f"[MEMORY EXTRACT ERROR] {e}")

def log_conversation_turn(user_message: str, bot_response: str, intent: str = "chat"):
    """Log to daily log file"""
    msg_clean = user_message.strip()
    if msg_clean == "[ACTION]" or msg_clean.startswith("<ACTION>") or msg_clean.startswith("[SYSTEM]") or msg_clean.startswith("[BACKGROUND]"):
        return

    if bot_response.startswith("write_file:") or \
       bot_response.startswith("run_shell") or \
       bot_response.startswith("read_file:") or \
       bot_response.startswith("run_python"):
        return

    # Concept: Object-Oriented Directory Path Creation
    # Why it exists: Simplified from the legacy os.makedirs to maintain Path standard.
    # What it solves: Eliminates importing/relying on legacy os functions for filesystem mutations.
    DAILY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    max_response_length = 500
    if len(bot_response) > max_response_length:
        truncated = bot_response[:max_response_length]
        last_period = max(truncated.rfind('. '), truncated.rfind('! '), truncated.rfind('? '))
        bot_response = truncated[:last_period+1] + "..." if last_period > 200 else truncated + "..."
    
    log_path = get_daily_log_path()
    time_now = datetime.now().strftime("%H:%M IST")
    
    entry = (f"\n## [{time_now}]\n**User:** {user_message}\n**Bot:** {bot_response}\n**Intent:** {intent}\n---\n")
    
    try:
        with open(log_path, 'a') as f:
            f.write(entry)
    except Exception as e:
        print(f"[LOG ERROR] {e}")
