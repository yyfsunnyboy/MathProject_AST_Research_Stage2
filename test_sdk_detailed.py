import os
import sys

# Set API Key
os.environ['GEMINI_API_KEY'] = 'AIzaSyBL3Yw3d3a5zT5C_OGQ5_drfLk5Q68DrWI'

# Add project root to path
sys.path.insert(0, r'E:\Python\MathProject_AST_Research')

print("=" * 70)
print("Testing New SDK Initialization")
print("=" * 70)

try:
    from google import genai as new_genai
    print("✅ New SDK imported successfully")
    
    api_key = os.environ.get('GEMINI_API_KEY')
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Try to create client
    client = new_genai.Client(api_key=api_key, http_options={'timeout': 300})
    print(f"✅ Client created: {type(client)}")
    
except Exception as e:
    print(f"❌ New SDK failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Testing GoogleAIClient from ai_wrapper")
print("=" * 70)

try:
    from core.ai_wrapper import GoogleAIClient
    client = GoogleAIClient('gemini-3-flash-preview', 0.1, max_tokens=65536)
    print(f"✅ GoogleAIClient created")
    print(f"   SDK Type: {'New' if client.is_new_sdk else 'Old'}")
    
except Exception as e:
    print(f"❌ GoogleAIClient failed: {e}")
    import traceback
    traceback.print_exc()
