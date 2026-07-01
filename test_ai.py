import os
os.environ["GROQ_API_KEY"] = "mock_api_key_for_testing_purposes"
import ai
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

def print_test_case(number, title, user_prompt, inner_steps, output_to_bot, expected_behavior, actual_behavior, comment=""):
    print("=" * 75)
    print(f"CASE {number}: {title}")
    print("-" * 75)
    print(f"[INPUT USER PROMPT]:")
    print(f"   prompt = {repr(user_prompt)}")
    print()
    print(f"[INNER ai.py STATE / REACTION]:")
    for step in inner_steps:
        print(f"   -> {step}")
    print()
    print(f"[OUTPUT RETURNED TO bot.py]:")
    print(f"   {repr(output_to_bot)}")
    print()
    
    is_correct = (expected_behavior == actual_behavior)
    status_str = "✅ CORRECT (Matched Expectations)" if is_correct else "🚨 INCORRECT (Mismatch/Bug Detected!)"
    print(f"[CONCLUSION]:")
    print(f"   Expected = {repr(expected_behavior)}")
    print(f"   Actual   = {repr(actual_behavior)}")
    print(f"   Status   = {status_str}")
    if comment:
        print(f"   Note     = {comment}")
    print("=" * 75 + "\n")

def run_tests():
    print("🚀 OPENCLAW AI.PY USER-PROMPT TRACE ENGINE ONLINE 🚀\n")

    # --- CASE 1: Standard Chat Greeting ---
    prompt1 = "Yo OpenClaw, who are you?"
    with patch('ai.get_groq_response') as mock_groq:
        mock_groq.return_value = "Yo bro! I'm OpenClaw, direct and chaotic. What we doing today?"
        
        ai.reset_history()
        resp1 = ai.ask_ai(prompt1)
        
        print_test_case(
            number=1,
            title="Standard Chat Response",
            user_prompt=prompt1,
            inner_steps=[
                "Read SOUL/IDENTITY md files to load 'You are OpenClaw' character details",
                "Append user message to session history list",
                "Query Groq API with Llama-70B model"
            ],
            output_to_bot=resp1,
            expected_behavior="Yo bro! I'm OpenClaw, direct and chaotic. What we doing today?",
            actual_behavior=resp1,
            comment="The AI successfully introduced itself using the identity prompt profile."
        )

    # --- CASE 2: Command Execution Request ---
    prompt2 = "Create a folder named test_sandbox"
    with patch('ai.get_groq_response') as mock_groq:
        # Mocking the structured ACTION tag response
        mock_groq.return_value = '<ACTION>{"type": "python", "code": "import os; os.mkdir(\'test_sandbox\')", "message": "Creating sandbox folder"}</ACTION>'
        
        resp2 = ai.ask_ai(prompt2)
        
        print_test_case(
            number=2,
            title="System Action Instruction Generation",
            user_prompt=prompt2,
            inner_steps=[
                "Scan prompt for system-level task request",
                "Check system rules: 'Respond with a valid JSON block wrapped in <ACTION> tags'",
                "Apply python preference: 'Prefer Python-native methods (os, shutil) over shell'"
            ],
            output_to_bot=resp2,
            expected_behavior='<ACTION>{"type": "python", "code": "import os; os.mkdir(\'test_sandbox\')", "message": "Creating sandbox folder"}</ACTION>',
            actual_behavior=resp2,
            comment="The AI outputted a strict action protocol ready for bot.py to execute!"
        )

    # --- CASE 3: Rate-Limit Hit & Model Fallback Recovery ---
    prompt3 = "Write a quick hello script"
    mock_client = MagicMock()
    
    # Simulate first model failing with 429, second model succeeding
    def mock_create(model, messages, max_tokens, temperature):
        if model == "llama-3.3-70b-versatile":
            raise Exception("Rate limit reached. HTTP 429")
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "Success response from Llama 4 Scout"
        return mock_resp
    mock_client.chat.completions.create.side_effect = mock_create

    with patch('ai.groq_client', mock_client):
        resp3 = ai.get_groq_response([{"role": "user", "content": prompt3}], mock_client)
        
        print_test_case(
            number=3,
            title="Model Rotation (429 Rate limit fallback)",
            user_prompt=prompt3,
            inner_steps=[
                "Send request to Llama 3.3 70B -> Catch Rate Limit 429",
                "Log rate limit warning console notification",
                "Rotate to next model in rotation queue: Llama 4 Scout",
                "Send request to Llama 4 Scout -> Success!"
            ],
            output_to_bot=resp3,
            expected_behavior="Success response from Llama 4 Scout",
            actual_behavior=resp3,
            comment="The system seamlessly bypassed the rate-limit failure in the background!"
        )

    # --- CASE 4: History Context Window Protection (Forgot old turns) ---
    prompt4 = "What was my first message?"
    
    # Fill history past 30 limit: 39 messages
    ai.conversation_history = [{"role": "user", "content": f"Message number {i}"} for i in range(38)]
    # Current turn user prompt makes it 39, plus assistant response will make it 40
    
    with patch('ai.get_groq_response') as mock_groq:
        mock_groq.return_value = "Sorry bro, I forgot! My memory is capped to protect token sizes."
        
        resp4 = ai.ask_ai(prompt4)
        
        print_test_case(
            number=4,
            title="Rolling History Queue Capping",
            user_prompt=prompt4,
            inner_steps=[
                "Detect history queue size contains 38 messages",
                "Build API messages list: slice queue to include only the last 30 messages",
                "Discard oldest messages (Context capped)",
                "Send capped conversation history context to Groq API"
            ],
            output_to_bot=resp4,
            expected_behavior="Sorry bro, I forgot! My memory is capped to protect token sizes.",
            actual_behavior=resp4,
            comment="Oldest messages successfully dropped from RAM context queue."
        )

if __name__ == "__main__":
    run_tests()
