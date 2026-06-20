import execution
from unittest.mock import patch, MagicMock

def run_tests():
    print("🚀 ANTIGRAVITY ENGINE: Booting Test Suite...\n")

    # --- BLOCK 1: The Blacklist (Real Execution) ---
    print("🧪 Test 1: Testing Blacklist...")
    res1 = execution.run_command("rm -rf /")
    assert res1["success"] == False, "ERROR: Blacklist failed!"
    assert "bruh" in res1["output"], "ERROR: Blacklist message missing!"
    print("✅ Test 1 Passed: Blacklist works.\n")

    # --- BLOCK 2: The Stunt Double (Mocking Success) ---
    print("🧪 Test 2: Testing Standard Success...")
    with patch('subprocess.run') as mock_subprocess:
        # Build the fake OS response
        fake_result = MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = "Everything is great!"
        fake_result.stderr = ""
        mock_subprocess.return_value = fake_result

        # Run the command
        res2 = execution.run_command("fake_command")
        assert res2["exit_code_success"] == True, "ERROR: Should be success."
        print("✅ Test 2 Passed: Mocked success works.\n")

    # --- BLOCK 3: THE FATAL FLAW (Proving the Bug) ---
    print("🧪 Test 3: Exposing the AI Slop...")
    with patch('subprocess.run') as mock_subprocess:
        fake_result = MagicMock()
        fake_result.returncode = 0  # OS says SUCCESS!
        fake_result.stdout = "I successfully fixed the Error: yesterday." 
        fake_result.stderr = ""
        mock_subprocess.return_value = fake_result

        res3 = execution.run_command("fake_command")
        
        print(f"   [OS TRUTH]: Did it succeed? {res3['exit_code_success']}")
        print(f"   [BOT'S GUESS]: Did it succeed? {res3['success']}")
        
        if res3["success"] == False:
            print("🚨 BUG PROVEN! The bot ignored the OS because it read 'Error:'!")
        
        print("✅ Test 3 Complete: Flaw exposed.\n")

if __name__ == "__main__":
    run_tests()
