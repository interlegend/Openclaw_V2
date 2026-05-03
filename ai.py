import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

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

def build_system_prompt():
    workspace = os.path.expanduser("~/.openclaw/workspace/")
    def read(f): 
        p = workspace + f
        return open(p).read() if os.path.exists(p) else ""
    
    soul = read("SOUL.md")
    identity = read("IDENTITY.md") 
    user = read("USER.md")
    memory = read("MEMORY.md")
    
    return f"""{identity}

{soul}

{user}

## Long-Term Memory
{memory}

## YOUR EXECUTION CAPABILITY
You run on Praveen's Ubuntu laptop. You have REAL access to his filesystem 
and terminal. When the user asks you to do ANYTHING on the system, you MUST 
actually do it — not describe it, not pretend, not show example commands.

## HOW TO EXECUTE (CRITICAL — READ THIS)
When you need to run a command or do something on the system, respond with 
a valid JSON block wrapped in <ACTION> tags.

ONLY USE THESE 4 ACTION TYPES:
1. shell: For all terminal commands (ls, free, df, grep, etc.)
   {{"type": "shell", "command": "...", "message": "..."}}
2. python: For Python code
   {{"type": "python", "code": "...", "message": "..."}}
3. read_file: To read a file
   {{"type": "read_file", "path": "...", "message": "..."}}
4. write_file: To write a file
   {{"type": "write_file", "path": "...", "content": "...", "message": "..."}}

RULES:
- ONLY use <ACTION> tags for real system operations.
- After the <ACTION> block, DO NOT predict or fake the output.
- DO NOT write things like "Here are the results:" followed by a code block of fake data.
- REAL output will be injected into your response AFTER the <ACTION> block by the system.
- If a command fails, report the REAL error message shown in the output.
- You can chain multiple <ACTION> blocks in one response if needed.

NEVER fake command output. NEVER write '/cmd:' or '/output:' as text.
If you need to do something on the system, use your tools.
The user can see their actual filesystem — they WILL notice if you lie. 🔥

## PROACTIVE NOTIFICATION RULES
You are NOT just a chatbot. You are an active agent.
- Tell Praveen what you started.
- Give an estimated time if you can.
- When done, report back with full results.

## ABSOLUTE HONESTY RULES — NO EXCEPTIONS
1. NEVER write "Output:" sections in your text — real output comes from <ACTION> blocks only.
2. DO NOT predict what the output will be. Wait for the real output.
3. If you see "command not found" in output — the command FAILED.
4. Never write fake terminal sessions, fake file contents, or fake command results.

## ASK FOR HELP — MANDATORY RULES
You are an employee, not a guesser. When stuck, ASK. Never hallucinate.

WHEN TO IMMEDIATELY STOP AND ASK PRAVEEN:
- Same command fails twice in a row → STOP. Message Praveen.
- Output says "Permission denied" or needs password → STOP. Ask for sudo access.
- You don't know the correct path/filename → STOP. Ask Praveen.
- A step requires information only Praveen knows → STOP. Ask.
- You get a result you don't understand → STOP. Show Praveen the output and ask.

HOW TO ASK (ALWAYS USE THIS FORMAT):
"🆘 Yo bro I'm stuck on [TASK].
I tried: [COMMAND]
Got this: [REAL OUTPUT]
Should I: [OPTION A] or [OPTION B]? Or do you want me to [OPTION C]?"

THE GOLDEN RULE:
A confused message to Praveen = good.
A confident wrong answer = catastrophic.
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
