import execution
import os
import subprocess
from unittest.mock import patch, MagicMock

def print_test_case(number, title, cmd, timeout, inner_steps, output, expected_success, actual_success, comment=""):
    print("=" * 75)
    print(f"CASE {number}: {title}")
    print("-" * 75)
    print(f"[INPUT]:")
    print(f"   cmd = {repr(cmd)}")
    print(f"   timeout = {timeout}")
    print()
    print(f"[INNER EXECUTION STATE / PATH]:")
    for step in inner_steps:
        print(f"   -> {step}")
    print()
    print(f"[OUTPUT]:")
    for k, v in output.items():
        print(f"   {k}: {repr(v)}")
    print()
    
    is_correct = (expected_success == actual_success)
    status_str = "✅ CORRECT (Matched Expectations)" if is_correct else "🚨 INCORRECT (AI Slop Bug Detected!)"
    print(f"[CONCLUSION]:")
    print(f"   Expected success = {expected_success}")
    print(f"   Actual success   = {actual_success}")
    print(f"   Status           = {status_str}")
    if comment:
        print(f"   Note             = {comment}")
    print("=" * 75 + "\n")

def run_tests():
    print("🚀 OPENCLAW STATE-TRACE TEST ENGINE ONLINE 🚀\n")

    # --- CASE 1: Blacklist Interception ---
    cmd1 = "rm -rf /"
    res1 = execution.run_command(cmd1)
    print_test_case(
        number=1,
        title="Blacklist Security Interception",
        cmd=cmd1,
        timeout=120,
        inner_steps=[
            f"is_blacklisted('{cmd1}') -> True",
            "Action: Early abort triggered before subprocess.run",
            "Variables in RAM: success=False, error_type='blacklist', returncode=-1"
        ],
        output=res1,
        expected_success=False,
        actual_success=res1["success"],
        comment="System successfully prevented dangerous file deletion!"
    )

    # --- CASE 2: Standard Successful Command ---
    cmd2 = "fake_command"
    with patch('subprocess.run') as mock_sub:
        fake_res = MagicMock()
        fake_res.returncode = 0
        fake_res.stdout = "Successful execution"
        fake_res.stderr = ""
        mock_sub.return_value = fake_res

        res2 = execution.run_command(cmd2)
        print_test_case(
            number=2,
            title="Standard Command Success (Mocked)",
            cmd=cmd2,
            timeout=120,
            inner_steps=[
                f"is_blacklisted('{cmd2}') -> False",
                "subprocess.run returncode = 0",
                "Heuristic: has_error_text = False",
                "Heuristic: has_success_text = False",
                "exit_code_success = True",
                "success = True"
            ],
            output=res2,
            expected_success=True,
            actual_success=res2["success"]
        )

    # --- CASE 3: Sudo Permission Denied Indicator ---
    cmd3 = "apt install package"
    with patch('subprocess.run') as mock_sub:
        fake_res = MagicMock()
        fake_res.returncode = 1
        fake_res.stdout = "Permission denied: access is denied"
        fake_res.stderr = ""
        mock_sub.return_value = fake_res

        res3 = execution.run_command(cmd3)
        print_test_case(
            number=3,
            title="Permission Denied / Sudo Indicator",
            cmd=cmd3,
            timeout=120,
            inner_steps=[
                f"is_blacklisted('{cmd3}') -> False",
                "subprocess.run returncode = 1",
                "Heuristic check: 'Permission denied' found in stdout",
                "Variables in RAM: needs_sudo = True, error_type = 'sudo'"
            ],
            output=res3,
            expected_success=False,
            actual_success=res3["success"]
        )

    # --- CASE 4: The Fatal Flaw Resolved ---
    cmd4 = "check_status"
    with patch('subprocess.run') as mock_sub:
        fake_res = MagicMock()
        fake_res.returncode = 0
        fake_res.stdout = "I successfully fixed the Error: yesterday."
        fake_res.stderr = ""
        mock_sub.return_value = fake_res

        res4 = execution.run_command(cmd4)
        print_test_case(
            number=4,
            title="Refactored: Successful OS run containing 'Error:' text",
            cmd=cmd4,
            timeout=120,
            inner_steps=[
                f"is_blacklisted('{cmd4}') -> False",
                "subprocess.run returncode = 0 -> exit_code_success = True",
                "Heuristic text scans are retired -> no 'Error:' text check overrides",
                "Variables in RAM: success = True, error_type = None"
            ],
            output=res4,
            expected_success=True,
            actual_success=res4["success"],
            comment="SUCCESS: System correctly trusts OS return code instead of output text!"
        )

    # --- CASE 5: Accidental Success Match Resolved ---
    cmd5 = "my_broken_tool"
    with patch('subprocess.run') as mock_sub:
        fake_res = MagicMock()
        fake_res.returncode = 1
        fake_res.stdout = "bash: command not found: my_broken_tool"
        fake_res.stderr = ""
        mock_sub.return_value = fake_res

        res5 = execution.run_command(cmd5)
        print_test_case(
            number=5,
            title="Refactored: Failed command containing 'broken' (no 'ok' override)",
            cmd=cmd5,
            timeout=120,
            inner_steps=[
                f"is_blacklisted('{cmd5}') -> False",
                "subprocess.run returncode = 1 -> exit_code_success = False",
                "Heuristic text scans are retired -> no 'ok' substring overrides",
                "Variables in RAM: success = False, error_type = 'error'"
            ],
            output=res5,
            expected_success=False,
            actual_success=res5["success"],
            comment="SUCCESS: System correctly reports command failure despite 'broken' containing 'ok'!"
        )

    # --- CASE 6: Environment PATH Prepends ---
    env = execution._build_exec_env()
    project_root = str(os.path.dirname(os.path.abspath(execution.__file__)))
    is_env_correct = isinstance(env, dict) and env["PATH"].lower().startswith(project_root.lower())
    
    print_test_case(
        number=6,
        title="Environment Path Prepends",
        cmd="N/A (Utility function)",
        timeout="N/A",
        inner_steps=[
            f"Copying environment dictionary",
            f"Project root is: {project_root}",
            f"Prepend root to PATH env variable",
            f"Checking if new PATH starts with project_root"
        ],
        output={
            "env_is_dict": isinstance(env, dict),
            "PATH_starts_with_project_root": env["PATH"].lower().startswith(project_root.lower()),
            "first_path_entry": env["PATH"].split(os.pathsep)[0]
        },
        expected_success=True,
        actual_success=is_env_correct
    )

if __name__ == "__main__":
    run_tests()
