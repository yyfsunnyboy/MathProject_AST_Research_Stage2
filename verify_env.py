
import sys
import os
sys.path.append(os.getcwd())
from config import Config

print("=== Check SDK ===")
try:
    import google.genai
    print("google.genai (New SDK) is INSTALLED.")
    print(f"Version: {google.genai.__version__ if hasattr(google.genai, '__version__') else 'Unknown'}")
except ImportError:
    print("google.genai (New SDK) is NOT installed.")

try:
    import google.generativeai
    print("google.generativeai (Old SDK) is INSTALLED.")
except ImportError:
    print("google.generativeai (Old SDK) is NOT installed.")

print("\n=== Check Config ===")
c = Config.CODER_PRESETS.get('gemini-2.5-flash')
if c:
    print(f"Preset found: gemini-2.5-flash")
    print(f"Max Tokens: {c.get('max_tokens')}")
    print(f"Safety Settings Present: {'safety_settings' in c}")
    if 'safety_settings' in c:
        print(f"Safety Settings Content: {c['safety_settings']}")
else:
    print("gemini-2.5-flash preset missing.")
