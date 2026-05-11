import subprocess
import os
import re
import sys

BLACKLIST = [
    "rm -rf /", "rm -rf ~", "mkfs", "dd if=", ":(){ :|:& };:", "deltree", "format c:"
]

SUDO_INDICATORS = [
    "sudo:", "password for", "authentication failure",
    "[sudo]", "Permission denied", "Operation not permitted",
    "access is denied"
]

ERROR_INDICATORS = [
    "command not found", "No such file or directory",
    "Error:", "ERROR:", "error:", "Traceback",
    "ModuleNotFoundError", "ImportError", "FileNotFoundError",
    "Connection refused", "timeout", "FAILED", "failed"
]

SUCCESS_INDICATORS = [
    "Successfully installed", "Already up to date",
    "done", "OK", "Created", "Saved", "written",
    "started", "running", "active"
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

def run_shell(command, timeout=30):
    if is_blacklisted(command):
        return None, "bruh absolutely not 💀 I have self-preservation instincts unlike you"
    
    try:
        env = os.environ.copy()
        project_root = str(Path(__file__).parent.resolve())
        
        # Add project root and a local bin folder to PATH for portability
        local_bin = str(Path(__file__).parent / "bin")
        env["PATH"] = f"{project_root}{os.pathsep}{local_bin}{os.pathsep}{env.get('PATH', '')}"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        output = result.stdout + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n... [truncated]"
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Command timed out after 30 seconds."
    except Exception as e:
        return None, str(e)

def run_python(code, timeout=30):
    if is_blacklisted(code):
        return None, "bruh absolutely not 💀 I have self-preservation instincts unlike you"
    
    try:
        # Cross-platform safe python execution
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n... [truncated]"
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Command timed out after 30 seconds."
    except Exception as e:
        return None, str(e)
        if len(output) > 4000:
            output = output[:4000] + "\n... [truncated]"
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Python execution timeout."
    except Exception as e:
        return None, str(e)

# === NEW STRUCTURED RUNNER ===
def run_command(cmd: str, timeout: int = 120) -> dict:
    """
    Execute command and return structured result with success detection.
    Returns dict with: output, success, needs_sudo, error_type
    """
    if is_blacklisted(cmd):
        return {
            "output": "bruh absolutely not 💀 I have self-preservation instincts unlike you",
            "success": False,
            "needs_sudo": False,
            "returncode": -1,
            "error_type": "blacklist"
        }

    env = os.environ.copy()
    project_root = str(Path(__file__).parent.resolve())
    local_bin = str(Path(__file__).parent / "bin")
    env["PATH"] = f"{project_root}{os.pathsep}{local_bin}{os.pathsep}{env.get('PATH', '')}"
    
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout, env=env
        )
        
        # Detect silent success first
        if is_silent_success_command(cmd) and result.returncode == 0:
            return {
                "output": "(silent success — no output expected)",
                "success": True,
                "needs_sudo": False,
                "returncode": 0,
                "error_type": None
            }

        combined_output = result.stdout.strip()
        if result.stderr.strip():
            combined_output += f"\n[stderr]: {result.stderr.strip()}"
        
        output = combined_output if combined_output else "(command returned no output)"
        
        # Detect success/failure
        output_lower = output.lower()
        needs_sudo = any(ind.lower() in output_lower for ind in SUDO_INDICATORS)
        has_error = result.returncode != 0 or any(ind.lower() in output_lower for ind in ERROR_INDICATORS)
        has_success = any(ind.lower() in output_lower for ind in SUCCESS_INDICATORS)
        is_actually_success = (result.returncode == 0 and not any(ind.lower() in output_lower for ind in ERROR_INDICATORS)) or has_success
        
        return {
            "output": output,
            "success": is_actually_success,
            "needs_sudo": needs_sudo,
            "returncode": result.returncode,
            "error_type": "sudo" if needs_sudo else ("error" if not is_actually_success else None)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "output": f"Command timed out after {timeout}s",
            "success": False,
            "needs_sudo": False,
            "returncode": -1,
            "error_type": "timeout"
        }
    except Exception as e:
        return {
            "output": str(e),
            "success": False,
            "needs_sudo": False,
            "returncode": -1,
            "error_type": "exception"
        }

def run_python_code(code: str) -> str:
    output, error = run_python(code)
    if error:
        return f"Error: {error}"
    return output
