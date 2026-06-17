import os
import time
import logging
from pathlib import Path
import json
import psutil
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

import security
import execution
import system
import files
import ai
import memory

# Strict Environment Loading
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USERS = security.ALLOWED_USERS
PRAVEEN_CHAT_ID = security.get_admin_id()
START_TIME = datetime.now()

# Global app reference for notifications
app = None
executor = ThreadPoolExecutor(max_workers=3)

# Escalation & Progress Globals
_waiting_for_help = False
_current_stuck_task = ""
_failure_tracker = {}  # task_id -> failure_count
_command_attempts = {}  # command_hash -> attempt_count
MAX_RETRIES = 2  # After 2 failures, ask for help

# Task Tracking Globals
_current_task_steps = []  # [(label, output, success)]
_current_task_name = ""

# Model Selection Config
AVAILABLE_MODELS = {
    "1": ("llama-3.3-70b-versatile",    "🧠 Llama 3.3 70B  — best quality, 100k TPD"),
    "2": ("meta-llama/llama-4-scout-17b-16e-instruct", "🚀 Llama 4 Scout  — fast, 500k TPD"),
    "3": ("qwen/qwen3-32b",             "🔬 Qwen3 32B      — strong reasoning, 500k TPD"),
    "4": ("moonshotai/kimi-k2-instruct","🌙 Kimi K2        — balanced, 300k TPD"),
    "5": ("llama-3.1-8b-instant",       "⚡ Llama 3.1 8B   — fastest, 500k TPD"),
}

# Current session model
current_model = "llama-3.3-70b-versatile"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === UTILS ===

async def notify_praveen(message: str, parse_mode: str = "Markdown"):
    """
    Send a proactive message to Praveen without waiting for his input.
    """
    if app is None:
        logger.error("App not initialized for notification")
        return
        
    try:
        await app.bot.send_message(
            chat_id=PRAVEEN_CHAT_ID,
            text=message,
            parse_mode=parse_mode
        )
    except Exception as e:
        logger.error(f"[NOTIFY ERROR] {e}")

async def safe_send(update: Update, text: str):
    """Safely send message handling length limits and Markdown errors."""
    if not text: return
    if len(text) > 4000: text = text[:4000] + "\n... [TRUNCATED]"
    if text.count("```") % 2 != 0: text += "\n```"
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Markdown failed: {e}. Falling back to plain text.")
        clean_text = text.replace("```", "[code]").replace("`", "'")
        try:
            await update.message.reply_text(clean_text)
        except Exception as e2:
            logger.error(f"Fallback send failed: {e2}")
            await update.message.reply_text("bruh that response was way too messy 💀")

async def ask_for_help(
    task_description: str,
    what_i_tried: str,
    actual_error: str,
    task_id: str = None
):
    """
    Called when bot is stuck.
    """
    global _failure_tracker, _waiting_for_help, _current_stuck_task
    
    if task_id:
        _failure_tracker[task_id] = _failure_tracker.get(task_id, 0) + 1
    
    help_message = (
        f"🆘 *YO BRO I'M STUCK — NEED YOUR INPUT*\n\n"
        f"📋 *Task:* {task_description}\n\n"
        f"🔧 *What I tried:*\n`{what_i_tried}`\n\n"
        f"❌ *What happened:*\n`{actual_error}`\n\n"
        f"👇 *Options:*\n"
        f"-  Tell me what to do differently\n"
        f"-  Give me your sudo password\n"
        f"-  Tell me to skip this step\n\n"
        f"_Waiting for your response before I continue..._"
    )
    
    await notify_praveen(help_message)
    _waiting_for_help = True
    _current_stuck_task = task_description

async def run_command_streaming(
    command: str,
    task_label: str,
    timeout: int = 300
) -> dict:
    """
    Run a command and stream progress.
    """
    global _current_task_steps
    env = os.environ.copy()
    project_root = str(Path(__file__).parent.resolve())
    local_bin = str(Path(__file__).parent / "bin")
    env["PATH"] = f"{project_root}{os.pathsep}{local_bin}{os.pathsep}{env.get('PATH', '')}"
    
    # Send start notification ONLY for streaming commands
    await notify_praveen(
        f"⚙️ *Started:* `{task_label}`\n"
        f"_Running: `{command[:80]}`_"
    )
    
    start_time = asyncio.get_event_loop().time()
    
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    async def ping_while_running():
        while proc.returncode is None:
            await asyncio.sleep(10)
            if proc.returncode is None:
                elapsed = int(asyncio.get_event_loop().time() - start_time)
                await notify_praveen(
                    f"⏳ *Still working:* `{task_label}`\n"
                    f"_Elapsed: {elapsed}s..._"
                )
    
    ping_task = asyncio.create_task(ping_while_running())
    
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), 
            timeout=timeout
        )
        ping_task.cancel()
        
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        output = stdout.decode().strip()
        err = stderr.decode().strip()
        combined = output
        if err: combined += f"\n[stderr]: {err}"
        if not combined.strip(): combined = "(no output)"
        
        success = proc.returncode == 0
        
        # SELF-VERIFY: Store result but DO NOT notify_praveen here
        verification = await self_verify_output(command, combined, task_label, ai.groq_client)
        _current_task_steps.append((task_label, combined, verification["success"]))

        if not success:
            needs_sudo = "permission denied" in combined.lower() or "sudo" in combined.lower()
            if needs_sudo:
                await ask_for_help(task_description=task_label, what_i_tried=command, actual_error=f"Needs sudo/password:\n{combined[:500]}")
        
        return {
            "output": combined,
            "success": success,
            "returncode": proc.returncode,
            "needs_sudo": "permission denied" in combined.lower() or "sudo" in combined.lower(),
            "error_type": None if success else "error"
        }
    except asyncio.TimeoutError:
        try: proc.kill()
        except: pass
        ping_task.cancel()
        await notify_praveen(f"⏱️ *Timeout after {timeout}s:* `{task_label}`")
        return {"output": "Timeout", "success": False, "returncode": -1, "needs_sudo": False, "error_type": "timeout"}

# === SECURITY ===

async def restricted(update: Update, context: ContextTypes.DEFAULT_TYPE, command_type="COMMAND"):
    user_id = update.effective_user.id
    if not security.check_user(user_id):
        return False
    if security.get_lock() and command_type in ["SHELL_CMD", "PYTHON_EXEC", "FILE", "KILL"]:
        await update.message.reply_text("🔒 Command execution locked")
        return False
    return True

# === VERIFICATION & REPORTING ===

async def self_verify_output(
    command: str,
    output: str,
    task_context: str,
    groq_client
) -> dict:
    """
    Ask the AI to evaluate its own command output.
    """
    verification_prompt = f"""You are a strict output verifier. 
A command was run and produced output. Classify it honestly.

COMMAND: {command}
OUTPUT: {output[:800]}
TASK CONTEXT: {task_context}

Respond with EXACTLY this JSON format (no other text):
{{
  "success": true,
  "confident": true,
  "verdict": "one sentence summary of what happened",
  "should_ask_user": false,
  "reason_to_ask": ""
}}

Rules for classification:
- success=true: command achieved its goal
- success=false: command failed or produced errors  
- confident=true: you are 100% sure of the outcome
- Empty output from pkill/rm/mv/cp/mkdir = success
- "command not found" = success=false
- HTML/JSON response from curl = success=true"""

    try:
        response = await asyncio.to_thread(
            lambda: groq_client.chat.completions.create(
                model=ai.current_model,
                messages=[{"role": "user", "content": verification_prompt}],
                max_tokens=200,
                temperature=0.1
            )
        )
        result_text = response.choices[0].message.content.strip()
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        if json_start != -1:
            return json.loads(result_text[json_start:json_end])
    except Exception as e:
        logger.error(f"[VERIFY ERROR] {e}")
    
    return {
        "success": False,
        "confident": False, 
        "verdict": "Could not verify output",
        "should_ask_user": True,
        "reason_to_ask": "Verification failed"
    }

async def execute_and_report(command: str, task_label: str, groq_client):
    """Execute command, self-verify, then track the step."""
    global _current_task_steps
    
    result = execution.run_command(command)
    output = result["output"]
    
    verification = await self_verify_output(
        command=command,
        output=output,
        task_context=task_label,
        groq_client=groq_client
    )
    
    # TRACK THE STEP: This is used by send_completion_report later
    _current_task_steps.append((task_label, output, verification["success"]))
    
    # REMOVED: Individual notify_praveen() calls from here.
    # We now let send_completion_report() handle all proactive messaging.
    
    return output

async def send_completion_report(
    original_task: str,
    steps_completed: list,  # [(label, output, success)]
    groq_client
):
    """
    After ALL actions in a response are done, generate and send 
    a natural follow-up report based on what happened.
    """
    successes = [(l, o) for l, o, s in steps_completed if s]
    failures  = [(l, o) for l, o, s in steps_completed if not s]
    total = len(steps_completed)
    if total == 0: return

    steps_summary = "\n".join([f"{'SUCCESS' if s else 'FAILED'}: {label} → {output[:200]}" for label, output, s in steps_completed])
    
    if not failures:
        # === FULL SUCCESS PATH — 1 extra message ===
        report_prompt = f"""You are OpenClaw, Praveen's AI assistant bot.
You just completed a task successfully. Write a SHORT casual follow-up 
message to Praveen (max 3 sentences) summarizing what you did.

Sound like a real assistant reporting back — natural, not robotic.
No bullet lists. No markdown headers. Just casual text with emojis.
Don't say "I have successfully" — that's corporate speak.

Original task: {original_task[:200]}
Steps completed:
{steps_summary}

Write ONLY the message. Nothing else."""

        try:
            response = await asyncio.to_thread(
                lambda: groq_client.chat.completions.create(
                    model=ai.current_model,
                    messages=[{"role": "user", "content": report_prompt}],
                    max_tokens=150,
                    temperature=0.8
                )
            )
            report_msg = response.choices[0].message.content.strip()
        except Exception:
            report_msg = f"🐾 Done bro! Everything went clean. Let me know what's next."
        await notify_praveen(report_msg)
    
    else:
        # === FAILURE PATH — 2+ extra messages ===
        error_context = "\n".join([f"FAILED: {l} → {o[:300]}" for l, o in failures])
        explain_prompt = f"""You are OpenClaw, Praveen's AI assistant bot.
A command you ran just failed. Explain to Praveen in 2-3 sentences:
1. What failed and the technical root cause (be specific)
2. Whether this is a common/known issue or unexpected
Sound like a knowledgeable employee explaining a problem — direct and clear.
Use relevant emojis. No bullet lists.
Failed steps:
{error_context}
Write ONLY the explanation message. Nothing else."""

        try:
            response = await asyncio.to_thread(
                lambda: groq_client.chat.completions.create(
                    model=ai.current_model,
                    messages=[{"role": "user", "content": explain_prompt}],
                    max_tokens=200,
                    temperature=0.5
                )
            )
            explain_msg = response.choices[0].message.content.strip()
        except Exception:
            explain_msg = f"⚠️ Hit an error on a step. Check the output above bro."
        
        await notify_praveen(explain_msg)
        await asyncio.sleep(1.5)
        
        fix_prompt = f"""You are OpenClaw, Praveen's AI assistant bot.
Decide: can you fix this yourself, or do you need Praveen's input?
Failed steps:
{error_context}
If you CAN self-fix: write "I can try [specific alternative approach] — want me to go ahead? 🔧"
If you NEED Praveen: write "Yo bro I need your input — [specific question only Praveen can answer]"
Rules: ONE sentence maximum. Casual tone. End with appropriate emoji.
Write ONLY the message. Nothing else."""

        try:
            response = await asyncio.to_thread(
                lambda: groq_client.chat.completions.create(
                    model=ai.current_model,
                    messages=[{"role": "user", "content": fix_prompt}],
                    max_tokens=100,
                    temperature=0.3
                )
            )
            action_msg = response.choices[0].message.content.strip()
        except Exception:
            action_msg = "🆘 Need your input to continue bro — what should I try next?"
        
        await notify_praveen(action_msg)

# === ACTION PARSER ===

async def execute_with_escalation(command: str, task_description: str) -> str:
    import hashlib
    cmd_hash = hashlib.md5(command.encode()).hexdigest()[:8]
    attempt = _command_attempts.get(cmd_hash, 0) + 1
    _command_attempts[cmd_hash] = attempt
    return await execute_and_report(command, task_description, ai.groq_client)

async def parse_and_execute_actions(ai_response):
    action_pattern = re.compile(r'<ACTION>\s*(.*?)\s*</ACTION>', re.DOTALL)
    actions = action_pattern.findall(ai_response)
    if not actions: return ai_response
    
    final_response = ai_response
    for action_raw in actions:
        action_json = action_raw.strip()
        if "```json" in action_json: action_json = action_json.split("```json")[1].split("```")[0].strip()
        elif "```" in action_json: action_json = action_json.split("```")[1].split("```")[0].strip()

        try:
            action = json.loads(action_json)
            action_type = action.get("type")
            preview_msg = action.get("message", "executing...")
            
            replacement = ""
            if action_type == "shell":
                command = action.get("command", "")
                if execution.is_long_running(command):
                    asyncio.create_task(run_command_streaming(command, preview_msg))
                    replacement = f"🚀 *Launched with live progress:* `{command}`\n_I'll ping you every 10s bro!_"
                else:
                    real_output = await execute_with_escalation(command, preview_msg)
                    replacement = f"⚙️ {preview_msg}\n```\n$ {command}\n--- REAL OUTPUT START ---\n{real_output}\n--- REAL OUTPUT END ---\n```"
                memory.log_conversation_turn("[ACTION]", f"run_shell_command: {command}", "TOOL_CALL")
            elif action_type == "python":
                code = action.get("code", "")
                real_output = execution.run_python_code(code)
                replacement = f"🐍 {preview_msg}\n```\n--- REAL OUTPUT START ---\n{real_output}\n--- REAL OUTPUT END ---\n```"
                memory.log_conversation_turn("[ACTION]", f"run_python_code: {code}", "TOOL_CALL")
            elif action_type == "read_file":
                path = action.get("path", "")
                real_output = files.read_file_content(path)
                replacement = f"📂 {preview_msg}\n```\n--- REAL OUTPUT START ---\n{real_output}\n--- REAL OUTPUT END ---\n```"
                memory.log_conversation_turn("[ACTION]", f"read_file: {path}", "TOOL_CALL")
            elif action_type == "write_file":
                path = action.get("path", "")
                content = action.get("content", "")
                real_output = files.write_file_content(path, content)
                replacement = f"✅ {preview_msg} — {real_output}"
                memory.log_conversation_turn("[ACTION]", f"write_file: {path}", "TOOL_CALL")
            else:
                replacement = f"❓ Unknown action type: {action_type}"
        except Exception as e:
            replacement = f"⚠️ Action failed: {e}"
        
        final_response = final_response.replace(f"<ACTION>\n{action_raw}\n</ACTION>", replacement).replace(f"<ACTION>{action_raw}</ACTION>", replacement).replace(f"<ACTION>\r\n{action_raw}\r\n</ACTION>", replacement).replace(f"<ACTION>{action_raw.strip()}</ACTION>", replacement)
    
    final_response = re.sub(r'<ACTION>.*?</ACTION>', '[action executed]', final_response, flags=re.DOTALL)
    return final_response

# === HANDLERS ===

async def handle_model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /model command — show menu or switch model"""
    global current_model
    if not await restricted(update, context): return
    args = context.args
    if not args:
        menu_lines = "\n".join([f"{'▶️' if model == current_model else '  '} {num}. {desc}" for num, (model, desc) in AVAILABLE_MODELS.items()])
        await update.message.reply_text(f"🤖 *Current model:* `{current_model}`\n\n*Available models:*\n{menu_lines}\n\n_Switch with:_ `/model 1` through `/model 5`\n_Or by name:_ `/model qwen`", parse_mode="Markdown")
        return
    selection = args[0].lower()
    if selection in AVAILABLE_MODELS:
        new_model, desc = AVAILABLE_MODELS[selection]
        current_model = new_model
        ai.current_model = current_model
        await update.message.reply_text(f"✅ *Model switched!*\n{desc}\n\n_All future requests will use this model._", parse_mode="Markdown")
        return
    for num, (model, desc) in AVAILABLE_MODELS.items():
        if selection in model.lower():
            current_model = model
            ai.current_model = current_model
            await update.message.reply_text(f"✅ *Switched to:* `{model}`\n_{desc}_", parse_mode="Markdown")
            return
    await update.message.reply_text(f"❌ Unknown model: `{selection}`")

async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await restricted(update, context, "SHELL_CMD"): return
    command = " ".join(context.args)
    if not command:
        await update.message.reply_text("Usage: /cmd <command>")
        return
    await update.message.reply_text("⚙️ Running that...")
    result = execution.run_command(command)
    output = result["output"]
    security.log_command(update.effective_user.id, "SHELL_CMD", command, "SUCCESS" if result["success"] else "FAILED")
    resp = f"```\n$ {command}\n--- REAL OUTPUT START ---\n{output}\n--- REAL OUTPUT END ---\n```"
    await safe_send(update, resp)
    memory.log_conversation_turn(command, output, "SHELL_CMD")

async def py_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await restricted(update, context, "PYTHON_EXEC"): return
    code = " ".join(context.args)
    if not code:
        await update.message.reply_text("Usage: /py <python_code>")
        return
    await update.message.reply_text("🐍 Executing...")
    output = execution.run_python_code(code)
    security.log_command(update.effective_user.id, "PYTHON_EXEC", code, "SUCCESS")
    resp = f"```\n--- REAL OUTPUT START ---\n{output}\n--- REAL OUTPUT END ---\n```"
    await safe_send(update, resp)
    memory.log_conversation_turn(code, output, "PYTHON_EXEC")

async def ping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await restricted(update, context): return
    uptime = str(datetime.now() - START_TIME).split(".")[0]
    ram = psutil.virtual_memory()
    ram_avail = f"{ram.available / (1024**3):.2f} GB"
    summary = f"🏓 **Pong!**\n\n⏱ **Uptime:** {uptime}\n🤖 **Model:** {ai.current_model}\n🧠 **RAM Available:** {ram_avail}\n\n✅ System healthy and ready for chaos."
    await safe_send(update, summary)
    memory.log_conversation_turn("/ping", summary, "SYSTEM_INFO")

async def sys_handler(update, context):
    if not await restricted(update, context): return
    await safe_send(update, system.get_system_stats())

async def procs_handler(update, context):
    if not await restricted(update, context): return
    await safe_send(update, f"```\n{system.get_processes()}\n```")

async def read_handler(update, context):
    if not await restricted(update, context, "FILE"): return
    if not context.args: return
    content = files.read_file_content(context.args[0])
    await safe_send(update, f"```\n--- REAL OUTPUT START ---\n{content}\n--- REAL OUTPUT END ---\n```")

async def write_handler(update, context):
    if not await restricted(update, context, "FILE"): return
    if len(context.args) < 2: return
    result = files.write_file_content(context.args[0], " ".join(context.args[1:]))
    await update.message.reply_text(f"✅ {result}")

async def ls_handler(update, context):
    if not await restricted(update, context, "FILE"): return
    summary, error = files.list_dir(context.args[0] if context.args else "~")
    await safe_send(update, summary if not error else f"❌ {error}")

async def kill_handler(update, context):
    if not await restricted(update, context, "KILL"): return
    if not context.args:
        await update.message.reply_text("Usage: /kill <pid_or_name>")
        return
    
    target = " ".join(context.args)
    killed = []
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'] or ""
            if str(proc.pid) == target or (not target.isdigit() and target.lower() in name.lower()):
                proc.terminate()
                killed.append(f"{name} ({proc.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if killed:
        await safe_send(update, f"✅ Terminated:\n- " + "\n- ".join(killed))
    else:
        await update.message.reply_text(f"❌ No process found matching '{target}'")

async def reset_handler(update, context):
    if not await restricted(update, context): return
    ai.reset_history()
    await update.message.reply_text("🧹 Memory wiped.")

# === NL ROUTING ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _waiting_for_help, _current_stuck_task, _current_task_steps, _current_task_name
    if not await restricted(update, context): return
    user_text_original = update.message.text
    if not user_text_original: return
    user_text = user_text_original

    if not _current_task_steps: _current_task_name = user_text

    if _waiting_for_help:
        _waiting_for_help = False
        injected_context = f"[SYSTEM: Bot was stuck on '{_current_stuck_task}'. Praveen just replied with guidance. Use this to resume the task: {user_text}]"
        user_text = injected_context + "\n\nPraveen says: " + user_text
        _current_stuck_task = ""

    ai_response = ai.ask_ai(user_text)
    final_response = await parse_and_execute_actions(ai_response)
    await safe_send(update, final_response)
    
    if _current_task_steps:
        await send_completion_report(original_task=user_text_original, steps_completed=_current_task_steps, groq_client=ai.groq_client)
        _current_task_steps = []
        _current_task_name = ""

    asyncio.create_task(
        memory.extract_and_save_facts(
            user_message=user_text_original, 
            bot_response=final_response, 
            groq_client=ai.groq_client,
            current_model=ai.current_model
        )
    )
    memory.log_conversation_turn(user_text_original, final_response, "chat")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.effective_message: await update.effective_message.reply_text("bruh something went wrong internally 💀")

def main():
    if not TOKEN: return
    while True:
        application = None
        try:
            global app
            application = ApplicationBuilder().token(TOKEN).build()
            app = application
            application.add_handler(CommandHandler("model", handle_model_command))
            application.add_handler(CommandHandler("cmd", cmd_handler))
            application.add_handler(CommandHandler("py", py_handler))
            application.add_handler(CommandHandler("sys", sys_handler))
            application.add_handler(CommandHandler("procs", procs_handler))
            application.add_handler(CommandHandler("ping", ping_handler))
            application.add_handler(CommandHandler("read", read_handler))
            application.add_handler(CommandHandler("write", write_handler))
            application.add_handler(CommandHandler("ls", ls_handler))
            application.add_handler(CommandHandler("kill", kill_handler))
            application.add_handler(CommandHandler("reset", reset_handler))
            application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
            application.add_error_handler(error_handler)
            print("OpenClaw is online! 😤")
            application.run_polling(close_loop=False)
        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()
