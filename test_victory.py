import os
import json
import ai
import bot

def test_victory_action():
    print("🚀 Starting Victory Test...")
    
    # Simulate user message
    user_msg = 'yo create a file called victory.txt in my home folder with the text "tool calling fixed"'
    print(f"User Message: {user_msg}")
    
    # 1. Get AI Response
    print("🤖 Getting AI response...")
    ai_response = ai.ask_ai(user_msg)
    print(f"AI Response: {ai_response}")
    
    # 2. Parse and Execute
    print("⚙️ Parsing and executing actions...")
    final_response = bot.parse_and_execute_actions(ai_response)
    print(f"Final Response:\n{final_response}")
    
    # 3. Verify System State
    victory_path = os.path.expanduser("~/victory.txt")
    if os.path.exists(victory_path):
        with open(victory_path, 'r') as f:
            content = f.read()
        print(f"✅ victory.txt exists!")
        print(f"📄 Content: {content}")
        if "tool calling fixed" in content:
            print("🌟 TEST PASSED: Content matches!")
        else:
            print("❌ TEST FAILED: Content mismatch.")
    else:
        print("❌ TEST FAILED: victory.txt not found.")

if __name__ == "__main__":
    test_victory_action()
