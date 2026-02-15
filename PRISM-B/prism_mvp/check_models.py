import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
print(f"🔑 Testing Key: {api_key[:10]}...")

try:
    client = genai.Client(api_key=api_key)
    print("\n📋 Available Models for this Key:")
    
    # Simple loop to just print names
    # The new SDK returns an iterator of Model objects
    for m in client.models.list():
        # format is usually "models/gemini-1.5-flash"
        print(f"   - {m.name}")
            
    print("\n✅ Verification Complete.")
    
except Exception as e:
    print(f"\n❌ Connection Error: {e}")