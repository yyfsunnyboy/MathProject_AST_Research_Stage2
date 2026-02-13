
import sys
import os
from dotenv import load_dotenv

# Enable loading from .env
load_dotenv()

sys.path.append(os.getcwd())
try:
    from config import Config
except ImportError:
    print("❌ Config not found")
    sys.exit(1)

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ google.genai not found")
    sys.exit(1)

api_key = Config.GEMINI_API_KEY
if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")
    
if not api_key:
    print("❌ API Key missing in Config and Env")
    sys.exit(1)

print(f"✅ API Key Loaded: {api_key[:5]}...{api_key[-3:]}")

client = genai.Client(api_key=api_key)

# 1. List Models to verify 'gemini-2.5-flash' existence
print("\n=== Listing Models (Partial) ===")
try:
    # New SDK listing
    # client.models.list() returns an iterator of Model objects
    # We filter by 'generateContent' support
    models = list(client.models.list())
    found_2_5 = False
    for m in models:
        if 'gemini' in m.name:
            print(f"- {m.name} (Max Output: {getattr(m, 'output_token_limit', 'Unknown')})")
            if 'gemini-2.5-flash' in m.name:
                found_2_5 = True
                
    if not found_2_5:
        print("⚠️  WARNING: 'gemini-2.5-flash' NOT FOUND in model list!")
        print("   This might cause fallback behavior or errors.")
except Exception as e:
    print(f"⚠️  List models failed: {e}")

# 2. Test Generation
prompt = "Write a python function that prints numbers from 1 to 100. Then write a very long comment explaining history of mathematics (at least 500 words)."

# Use the exact config from config.py manually reconstructed
safety_settings_dicts = Config.CODER_PRESETS.get('gemini-2.5-flash', {}).get('safety_settings', [])
converted_safety = []
for s in safety_settings_dicts:
    converted_safety.append(
        types.SafetySetting(
            category=s['category'],
            threshold=s['threshold']
        )
    )

config_params = {
    "temperature": 0.1,
    "max_output_tokens": 8192,
    "safety_settings": converted_safety
}

print(f"\n=== Testing Generation with Model: gemini-2.5-flash ===")
print(f"Config: {config_params}")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config_params
    )
    
    txt = response.text
    print(f"\nResponse Length: {len(txt)}")
    print(f"Token Count (approx): {len(txt)//4}")
    
    if hasattr(response, 'candidates') and response.candidates:
        cand = response.candidates[0]
        print(f"Finish Reason: {cand.finish_reason}")
        
    print("\nFirst 100 chars:")
    print(txt[:100])
    print("\nLast 100 chars:")
    print(txt[-100:])

except Exception as e:
    print(f"\n❌ Generation Error: {e}")
