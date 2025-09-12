import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"🔍 DEBUG: OPENAI_API_KEY loaded: {'YES' if OPENAI_API_KEY else 'NO'}")
if OPENAI_API_KEY:
    print(f"🔍 DEBUG: API Key starts with: {OPENAI_API_KEY[:10]}...")
else:
    print("🔍 DEBUG: No API key found in environment variables")
    print("🔍 DEBUG: Available env vars:", [k for k in os.environ.keys() if 'OPENAI' in k or 'API' in k])

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")
