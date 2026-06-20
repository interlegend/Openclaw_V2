BROOOOO 😤🔥

You got me. I took a shortcut. I skipped the string formatting lines and the cross-file connections because I assumed they were "too simple." 

**That is the exact opposite of the protocol.** A Senior Engineer doesn't assume. If you are going to own this code, you need to understand the string paddings (`:<7`), the newline characters (`\n`), and exactly how modifying this file ripples out and blows up `bot.py` if we aren't careful.

I accept the roast. It makes the masterclass better. 

Here is the **Full, 100% Uncut 49-Line Source Code** of your file first, so you don't have to switch to VSCode. Then, we tear apart every single byte, including the cross-file architecture.

---

### 📄 THE FULL SOURCE CODE: `system.py`

```python
from pathlib import Path
import psutil
import time

def get_system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    
    # Cross-platform drive detection
    drive = Path.home().anchor or "C:\\"
    disk = psutil.disk_usage(drive)
    
    # Top 5 processes by CPU usage
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
    
    summary = f"📊 **System Stats**\n\n"
    summary += f"💻 **CPU:** {cpu_usage}%\n"
    summary += f"🧠 **RAM:** {ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB ({ram.percent}%)\n"
    summary += f"💾 **Disk:** {disk.used / (1024**3):.2f} GB / {disk.total / (1024**3):.2f} GB ({disk.percent}%)\n\n"
    summary += f"🔝 **Top 5 Processes:**\n"
    for p in top_processes:
        summary += f"- {p['name']} (PID: {p['pid']}): {p['cpu_percent']}%\n"
    
    return summary

def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    top_20 = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:20]
    
    summary = "📋 **Top 20 Processes by CPU:**\n\n"
    summary += f"{'PID':<7} {'Name':<20} {'CPU%':<7} {'RAM%':<7}\n"
    summary += "—" * 45 + "\n"
    for p in top_20:
        summary += f"{p['pid']:<7} {p['name'][:20]:<20} {p['cpu_percent']:<7.1f} {p['memory_percent']:<7.1f}\n"
    
    return summary
```

---

### 🌐 SYSTEM ARCHITECTURE: Cross-File Dependencies

Before we touch a line, you must know who relies on this file. 

```text
[ bot.py ]
    │
    ├─▶ Telegram command: /sys   ──▶ Calls: system.get_system_stats()
    │
    └─▶ Telegram command: /procs ──▶ Calls: system.get_processes()
```

**⚠️ ARCHITECTURAL WARNING:**
If we change the names of the functions `get_system_stats()` or `get_processes()` in this file, `bot.py` will throw an `ImportError` or `AttributeError` and crash the next time you type `/sys` or `/procs`. 
**The Rule:** We can gut and rewrite the *insides* of these functions all we want, but we MUST keep the function names exactly the same so `bot.py` doesn't break. This is called keeping the **API Contract** intact.

---

## ━━━━━━━━━━━━━━━━━━━━
## BLOCK 1: IMPORTS (Lines 1-3)
## ━━━━━━━━━━━━━━━━━━━━

```python
from pathlib import Path
import psutil
import time
```

### 📊 DATA FLOW VISUALIZATION
```text
Python Engine loads:
├─ Path   (From standard library: handles C:\ vs /home paths)
├─ psutil (From installed pip packages: reads motherboard/OS kernel)
└─ time   (From standard library: handles clocks)
```

### 🎓 BEGINNER EXPLANATION:
*   **`from pathlib import Path`**: Instead of importing a massive toolbox, we are importing one specific tool (`Path`) from the `pathlib` toolbox. It helps us navigate folders.
*   **`import psutil`**: Brings in the massive C-based library that talks directly to Windows/Linux hardware.
*   **`import time`**: Imports clock functions.

### 💾 RAM VIEW
```text
Path   -> <class 'pathlib.Path'>
psutil -> <module 'psutil'>
time   -> <module 'time'>
```

### 🕵️ OWNERSHIP MODE & AI SLOP DETECTOR
*   **What breaks?** Without `psutil`, Python cannot read CPU/RAM.
*   **Is this AI slop?** YES. Do a `Ctrl+F` for the word `time` in the 49 lines above. It is never used. The AI imported it and forgot about it.
*   **Decision:** 🟡 **MODIFY**. Delete `import time`.

---

## ━━━━━━━━━━━━━━━━━━━━
## BLOCK 2: STATS HARDWARE SETUP (Lines 5-11)
## ━━━━━━━━━━━━━━━━━━━━

```python
def get_system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    
    # Cross-platform drive detection
    drive = Path.home().anchor or "C:\\"
    disk = psutil.disk_usage(drive)
```

### 📊 RUNTIME HARDWARE POLLING
```text
psutil.cpu_percent ──(waits 1 sec)──▶ 45.2
psutil.virtual_memory ──────────────▶ (Object with .used, .total, .percent)
Path.home().anchor ─────────────────▶ "C:\" (Windows) OR "/" (Linux)
```

### 🎓 BEGINNER EXPLANATION:
*   **`interval=1`**: CPU usage must be measured over time. This pauses your program for exactly 1 second to watch the CPU, then returns a percentage (e.g., `12.5`).
*   **`Path.home().anchor`**: Finds the "root" of your hard drive so it knows where to check storage space. The `or "C:\\"` is a safety fallback: if it fails to find the root, it just guesses it's a Windows `C:` drive.

### 💾 RAM VIEW
```text
cpu_usage -> 12.5
ram       -> svmem(total=17179869184, used=8589934592, percent=50.0...)
drive     -> "C:\"
disk      -> sdiskusage(total=512110190592, used=..., percent=82.1)
```

### 🕵️ OWNERSHIP MODE
*   **Why does it exist?** Gathers the raw math required to build the Telegram message.
*   **Decision:** 🟢 **KEEP**. Good, cross-platform engineering.

---

## ━━━━━━━━━━━━━━━━━━━━
## BLOCK 3: PROCESS ITERATION (Lines 13-19)
## ━━━━━━━━━━━━━━━━━━━━

```python
    # Top 5 processes by CPU usage
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
```

### 📊 EXECUTION FLOW (RACE CONDITION DEFENSE)
```text
psutil lists all running programs on your PC:
├─ [Chrome]  ──> Append {'name':'chrome', 'cpu':2.0} to list
├─ [System]  ──> AccessDenied! ──> except triggers ──> 'pass' (Ignore)
└─ [Spotify] ──> Closes mid-scan! ──> NoSuchProcess! ──> 'pass' (Ignore)
```

### 🎓 BEGINNER EXPLANATION:
*   **`processes = []`**: Creates an empty list to store the data.
*   **`for proc in psutil...`**: A loop that goes through every running app on your computer.
*   **`try / except`**: The Operating System is alive. Apps open and close in milliseconds. If Python asks about "Spotify" but you closed Spotify a millisecond ago, the OS throws an error. The `try/except` block catches these specific errors.
*   **`pass`**: A Python keyword that means "Do absolutely nothing. Just move to the next item in the loop."

### 💾 RAM VIEW
```text
processes -> [
  {'pid': 1024, 'name': 'chrome.exe', 'cpu_percent': 2.1},
  {'pid': 500, 'name': 'python', 'cpu_percent': 15.0}
]
```

### 🕵️ OWNERSHIP MODE
*   **What breaks if removed?** The bot will crash randomly whenever a background app closes during the 1-second scan window. 
*   **Decision:** 🟢 **KEEP**. 

---

## ━━━━━━━━━━━━━━━━━━━━
## BLOCK 4: SORTING & FORMATTING (Lines 21-31)
## ━━━━━━━━━━━━━━━━━━━━

```python
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
    
    summary = f"📊 **System Stats**\n\n"
    summary += f"💻 **CPU:** {cpu_usage}%\n"
    summary += f"🧠 **RAM:** {ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB ({ram.percent}%)\n"
    summary += f"💾 **Disk:** {disk.used / (1024**3):.2f} GB / {disk.total / (1024**3):.2f} GB ({disk.percent}%)\n\n"
    summary += f"🔝 **Top 5 Processes:**\n"
    for p in top_processes:
        summary += f"- {p['name']} (PID: {p['pid']}): {p['cpu_percent']}%\n"
    
    return summary
```

### 📊 STRING BUILDER FLOW
```text
summary = "📊 Stats"
summary += " CPU..."   (Appends to the end)
summary += " RAM..."   (Appends to the end)
Returns one massive text block to bot.py
```

### 🎓 BEGINNER EXPLANATION:
*   **`sorted(..., key=lambda x: x['cpu_percent'], reverse=True)`**: This organizes the list. The `lambda` is a tiny, invisible function telling Python: "Look at the `cpu_percent` dictionary key to decide who wins." `reverse=True` puts the biggest numbers at the top.
*   **`[:5]` (List Slicing)**: Grabs only the first 5 items from the sorted list.
*   **`\n`**: This is a special character that tells Telegram to hit "Enter" (Start a new line).
*   **`+=` (Append Operator)**: Instead of writing `x = x + 2`, you write `x += 2`. Here, it adds text to the end of the `summary` string.
*   **`(1024**3)` & `:.2f`**: Computers read in Bytes. `1024**3` is math for Gigabytes. The `:.2f` formats the massive decimal to exactly 2 digits (e.g., `8.12 GB`).
*   **`for p in top_processes:`**: Loops through those 5 programs and formats them into a bulleted list string.

### 🕵️ OWNERSHIP MODE
*   **What problem does it solve?** Humans can't read raw dictionary data. This makes it a pretty Telegram message.
*   **Decision:** 🟢 **KEEP**. 

---

## ━━━━━━━━━━━━━━━━━━━━
## BLOCK 5 & 6: THE DUPLICATE `get_processes` (Lines 33-49)
## ━━━━━━━━━━━━━━━━━━━━

```python
def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        # [IDENTICAL TRY/EXCEPT BLOCK OMITTED FOR SPACE]
    
    top_20 = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:20]
    
    summary = "📋 **Top 20 Processes by CPU:**\n\n"
    summary += f"{'PID':<7} {'Name':<20} {'CPU%':<7} {'RAM%':<7}\n"
    summary += "—" * 45 + "\n"
    for p in top_20:
        summary += f"{p['pid']:<7} {p['name'][:20]:<20} {p['cpu_percent']:<7.1f} {p['memory_percent']:<7.1f}\n"
    
    return summary
```

### 📊 DATA FORMATTING FLOW
```text
Table Headers:
PID     Name                 CPU%    RAM%   
─────────────────────────────────────────────
1024    chrome               12.0    5.0
```

### 🎓 BEGINNER EXPLANATION: String Padding
*   **Why is the `for` loop copy-pasted?** The AI was lazy. It needed memory stats this time (`memory_percent`), so it just copy-pasted the entire loop from above.
*   **`{'PID':<7}`**: This is string alignment! It tells Python: "Print the word 'PID', but force it to take up exactly 7 spaces of width, aligned to the LEFT (`<`)." This is how you make beautiful columns that line up perfectly in text!
*   **`"—" * 45`**: Python lets you multiply strings! This prints a line of 45 dashes `────────────────` to separate the header from the data.
*   **`{p['name'][:20]:<20}`**: Grabs the app's name, cuts it off if it's longer than 20 characters (`[:20]`), and ensures it takes up exactly 20 spaces (`<20`).

### 🕵️ OWNERSHIP MODE & AI SLOP DETECTOR
*   **Is this AI slop?** 🔴 YES. **Violation of DRY (Don't Repeat Yourself).**
    The complex `psutil` loop is identical to the one in Block 3. If you ever found a bug in the process scanner, you would have to fix it twice. 
*   **How would a human engineer fix it?** Create *one* master internal function `_fetch_all_processes()` that gathers everything. Then `get_system_stats()` and `get_processes()` just call it and format the data.

### 🛠️ DECISION: MODIFY (Major Refactor)

---

# 📊 FINAL FILE SCORECARD: `system.py`

*   **Complexity Score:** 5/10
*   **Engineering Quality:** 6/10 (Great OS error handling, terrible code duplication).
*   **AI Slop Level:** 6/10
*   **Beginner Difficulty:** 6/10

✅ **Most Important Concepts Learned:**
1.  **Cross-file dependencies:** You cannot rename functions that other files import!
2.  **String padding (`<7`)** is how you build tables in text.
3.  **Code Duplication (DRY)** is the enemy of maintainability.

---

# 🛠️ THE HUMAN REWRITE CHALLENGE

We are going to fix the AI's duplication while **keeping the API contract intact** so `bot.py` doesn't crash.

**Your Blueprint (With Skeleton Hints):**

**1. Imports:** Get `Path` and `psutil`. (No `time`).

**2. The Master Function (New!):**
*(Note: Starting a function with `_` tells other engineers "this is for internal use only in this file.")*
```python
def _fetch_all_processes():
    processes = []
    # Write ONE for loop using psutil.process_iter. 
    # Grab ALL properties we might need: ['pid', 'name', 'cpu_percent', 'memory_percent']
    # Add the try/except block.
    # Return the processes list!
```

**3. The Stats Function (Must keep exact name!):**
```python
def get_system_stats():
    # 1. Grab cpu_usage, ram, and disk logic.
    
    # 2. Call your master function!
    all_procs = _fetch_all_processes()
    
    # 3. Sort all_procs by 'cpu_percent', reverse=True, slice [:5]
    
    # 4. Build the summary string (including the \n and += logic)
    # 5. return summary
```

**4. The Procs Function (Must keep exact name!):**
```python
def get_processes():
    # 1. Call your master function!
    all_procs = _fetch_all_processes()
    
    # 2. Sort all_procs by 'cpu_percent', reverse=True, slice [:20]
    
    # 3. Build the summary string using the cool :<7 alignment formatting!
    # 4. return summary
```

Write the code. Paste it here. You are officially doing structural refactoring. Let's see it. 😤💻