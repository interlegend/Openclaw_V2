import subprocess
import os
from pathlib import Path
import sys

BLACKLIST = [
    "rm -rf /", "rm -rf ~", "mkfs", "dd if=", ":(){ :|:& };:", "deltree", "format c:"
]

SUDO_INDICATORS = [
    "sudo:", "password for", "authentication failure",
    "[sudo]", "Permission denied", "Operation not permitted",
    "access is denied"
]


SILENT_SUCCESS_COMMANDS = [
    "pkill", "kill", "rm ", "mv ", "cp ", "mkdir", "touch",
    "chmod", "chown", "ln ", "unlink", "rmdir",
    "systemctl start", "systemctl stop", "systemctl restart",
    "echo ", "export ", "source ", "nohup ",
    "sleep ", "wait "
]

BACKGROUND_COMMANDS = [
    "pip install", "pip3 install", "apt install", "apt-get install",
    "npm install", "yarn install", "cargo build", "cargo install",
    "wget ", "curl -O", "curl -L", "git clone", "python3 setup.py",
    "make ", "cmake ", "docker build", "docker pull"
]

# Configuration constants
OUTPUT_TRUNCATE = 4000
DEFAULT_SHELL_TIMEOUT = 30
DEFAULT_CMD_TIMEOUT = 120


def _build_exec_env() -> dict:
    """Return an environment dict with project root and local bin prepended to PATH."""
    env = os.environ.copy()
    project_root = str(Path(__file__).parent.resolve())
    local_bin = str(Path(__file__).parent / "bin")
    env["PATH"] = f"{project_root}{os.pathsep}{local_bin}{os.pathsep}{env.get('PATH', '')}"
    return env

def is_blacklisted(command):
    cmd_lower = command.lower()
    for item in BLACKLIST:
        if item in cmd_lower:
            return True
    return False

def is_silent_success_command(cmd: str) -> bool:
    """These commands succeed silently — no output = success"""
    cmd_stripped = cmd.strip().lower()
    return any(cmd_stripped.startswith(sc) for sc in SILENT_SUCCESS_COMMANDS)

def is_long_running(command: str) -> bool:
    cmd_lower = command.lower().strip()
    return any(cmd_lower.startswith(bg) for bg in BACKGROUND_COMMANDS)

def run_shell(command, timeout: int = DEFAULT_SHELL_TIMEOUT):
    """Legacy convenience: execute a shell command and return (output, error).

    This function is kept for backwards compatibility but delegates to
    `run_command` and maps the structured dict back to the older tuple contract.
    """
    if is_blacklisted(command):
        return None, "bruh absolutely not 💀 I have self-preservation instincts unlike you"

    result = run_command(command, timeout=timeout)
    if result.get("error_type") is not None and not result.get("success", False):
        return None, result.get("output")
    return result.get("output"), None

def run_python(code: str, timeout: int = DEFAULT_SHELL_TIMEOUT):
    """Legacy convenience: execute Python code and return (output, error).

    Delegates to `run_command` using the current Python interpreter. Returns
    a tuple for backwards compatibility.
    """
    if is_blacklisted(code):
        return None, "bruh absolutely not 💀 I have self-preservation instincts unlike you"

    cmd = [sys.executable, "-c", code]
    result = run_command(cmd, timeout=timeout)
    if result.get("error_type") is not None and not result.get("success", False):
        return None, result.get("output")
    return result.get("output"), None

# === NEW STRUCTURED RUNNER ===
def run_command(cmd, timeout: int = DEFAULT_CMD_TIMEOUT) -> dict:
    """Unified execution engine.

    - `cmd` may be a string (shell=True) or a list/tuple (args, shell=False).
    - Returns a structured dict with consistent keys used across the system.

    Compatibility: We preserve the original `success` semantics used by callers
    while also exposing `exit_code_success` and `heuristic_success` so future
    callers can prefer deterministic exit-code-based results.
    """
    # Blacklist check
    cmd_display = cmd if isinstance(cmd, str) else " ".join(cmd)
    if is_blacklisted(cmd_display):
        return {
            "output": "bruh absolutely not 💀 I have self-preservation instincts unlike you",
            "success": False,
            "exit_code_success": False,
            "heuristic_success": False,
            "needs_sudo": False,
            "returncode": -1,
            "error_type": "blacklist"
        }

    env = _build_exec_env()

    use_shell = isinstance(cmd, str)
    try:
        result = subprocess.run(
            cmd,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )

        # Normalize outputs
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        combined = stdout
        if stderr:
            combined += ("\n[stderr]: " + stderr) if combined else ("[stderr]: " + stderr)
        output = combined if combined else "(command returned no output)"
        if len(output) > OUTPUT_TRUNCATE:
            output = output[:OUTPUT_TRUNCATE] + "\n... [truncated]"

        output_lower = output.lower()

        # Heuristics
        needs_sudo = any(ind.lower() in output_lower for ind in SUDO_INDICATORS)

        # Deterministic exit-code result (authoritative)
        exit_code_success = (result.returncode == 0)

        return {
            "output": output,
            "success": exit_code_success,
            "exit_code_success": exit_code_success,
            "needs_sudo": needs_sudo,
            "returncode": result.returncode,
            "error_type": "sudo" if needs_sudo else ("error" if not exit_code_success else None)
        }

    except subprocess.TimeoutExpired:
        return {
            "output": f"Command timed out after {timeout}s",
            "success": False,
            "exit_code_success": False,
            "heuristic_success": False,
            "needs_sudo": False,
            "returncode": -1,
            "error_type": "timeout"
        }
    except Exception as e:
        return {
            "output": str(e),
            "success": False,
            "exit_code_success": False,
            "heuristic_success": False,
            "needs_sudo": False,
            "returncode": -1,
            "error_type": "exception"
        }

def run_python_code(code: str) -> str:
    output, error = run_python(code)
    if error:
        return f"Error: {error}"
    return output
