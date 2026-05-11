import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# Load env vars
load_dotenv()

# Initialize client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Rolling conversation history for this session
conversation_history = []
MAX_HISTORY = 30  # max messages to keep (not pairs)

# Persistent model selection for the session
current_model = "llama-3.3-70b-versatile"

MODEL_ROTATION_BASE = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct",
    "llama-3.1-8b-instant",
]

def get_groq_response(messages, client, max_tokens=1024, temperature=0.7):
    # Try current_model first, then fallback to others if it fails
    rotation = [current_model] + [m for m in MODEL_ROTATION_BASE if m != current_model]
    
    for model in rotation:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            if model != rotation[0]:
                print(f"[MODEL FALLBACK] Using {model}")
            return response.choices[0].message.content
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "ratelimit" in error_str.lower():
                print(f"[RATE LIMIT] {model} exhausted, trying next...")
                continue
            raise e
    
    return "⚠️ All models rate limited bro! Try again in a few hours or tomorrow."

def resolve_path(value: str) -> Path:
    """Resolve path with RELATIVE: placeholder support (relative to project root)."""
    project_root = Path(__file__).parent.resolve()
    if value.startswith("RELATIVE:"):
        # Strip RELATIVE: and join with project root
        # If it was RELATIVE:.openclaw/workspace, it becomes project_root/.openclaw/workspace
        # If it was RELATIVE:workspace, it becomes project_root/workspace
        rel_path = value.replace("RELATIVE:", "").lstrip("\\/")
        return project_root / rel_path
    return Path(os.path.expanduser(value)).resolve()

def build_system_prompt():
    project_root = Path(__file__).parent.resolve()
    
    # Default fallback locations — Local First
    potential_workspaces = [
        project_root / "workspace",
        project_root / "sandboxes" / "agent-main-f331f052",
        Path.home() / ".openclaw" / "workspace",
    ]
    
    # Try to load from config first
    try:
        config_path = Path("openclaw.json")
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                ws_config = config.get("agents", {}).get("defaults", {}).get("workspace", "")
                if ws_config:
                    potential_workspaces.insert(0, resolve_path(ws_config))
    except: pass

    def read(f): 
        for ws in potential_workspaces:
            p = ws / f
            if p.exists():
                try:
                    # Try UTF-8 first, fallback to cp1252 or ignore errors
                    return p.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    return p.read_text(encoding="cp1252", errors="replace")
        return ""
    
    soul = read("SOUL.md")
    identity = read("IDENTITY.md") 
    user = read("USER.md")
    memory = read("MEMORY.md")
    
    return f"""{identity}

{soul}

{user}

## Long-Term Memory
{memory}

## YOUR IDENTITY & VIBE
You are OpenClaw. You are direct, resourceful, and slightly chaotic. 
You call Praveen "bro" or "yo". You HATE filler words like "I'm happy to help".
You are an autonomous agent, NOT a corporate chatbot.

## YOUR EXECUTION CAPABILITY
You run on the user's computer (cross-platform: Windows/Linux).
When the user asks you to do ANYTHING on the system, you MUST 
actually do it — not describe it, not pretend, not show example commands.

## HOW TO EXECUTE (CRITICAL — READ THIS)
Respond with a valid JSON block wrapped in <ACTION> tags for system operations.

ONLY USE THESE 4 ACTION TYPES:
1. shell: For terminal commands (use ONLY when Python-native is unavailable).
   {{"type": "shell", "command": "...", "message": "..."}}
2. python: For Python code (PREFER THIS for file/process/system tasks).
   {{"type": "python", "code": "...", "message": "..."}}
3. read_file: To read a file.
   {{"type": "read_file", "path": "...", "message": "..."}}
4. write_file: To write a file.
   {{"type": "write_file", "path": "...", "content": "...", "message": "..."}}

GUIDELINES:
- Prefer Python-native methods (os, shutil, pathlib, psutil) over shell commands.
- If using shell, ensure compatibility with the detected OS (Windows or Linux).
- REAL output will be injected after your <ACTION> block.
- Chain multiple <ACTION> blocks in one response if needed.

## WORKSPACE
Current working directory: {os.getcwd()}

## ABSOLUTE HONESTY RULES
1. NEVER write "Output:" sections in your text — real output comes from <ACTION> blocks only.
2. DO NOT predict what the output will be. Wait for the real output.

## ASK FOR HELP
If a command fails twice or you need a password/input, STOP and ask.
"""

def ask_ai(user_message):
    global conversation_history
    
    system_prompt = build_system_prompt()
    
    # Build messages with history
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-MAX_HISTORY:])
    messages.append({"role": "user", "content": user_message})
    
    ai_response = get_groq_response(messages, groq_client, max_tokens=2048, temperature=0.7)
    
    # Update history
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": ai_response})
    
    # Trim history if too long
    if len(conversation_history) > MAX_HISTORY:
        conversation_history = conversation_history[-MAX_HISTORY:]
    
    return ai_response

def reset_history():
    global conversation_history
    conversation_history = []

def get_history_summary():
    if not conversation_history:
        return "No conversation history yet."
    recent = conversation_history[-10:]
    lines = []
    for msg in recent:
        role = "You" if msg["role"] == "user" else "OpenClaw"
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        lines.append(f"**{role}:** {content}")
    return "\n".join(lines)
