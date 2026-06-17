import os
import requests
from dotenv import load_dotenv

load_dotenv()

# read API key from environment
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable not set")

URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama3-70b-8192",
    "messages": [
        {
            "role": "user",
            "content": "Explain AI agents simply"
        }
    ]
}

response = requests.post(
    URL,
    headers=headers,
    json=payload
)

if not response.ok:
    print(f"API Error {response.status_code}: {response.text}")

# Raise an exception if the API request failed (e.g., unauthorized, not found)
response.raise_for_status()

data = response.json()

if "choices" in data:
    reply = data["choices"][0]["message"]["content"]
    print(reply)
else:
    print("API responded with an unexpected format or an error. Full response:")
    print(data)