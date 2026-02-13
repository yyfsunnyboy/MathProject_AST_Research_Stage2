
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import Config
except ImportError:
    print("❌ Critical: Cannot import Config. Run from project root or checks paths.")
    sys.exit(1)


try:
    # Try New SDK
    from google import genai
    HAS_NEW_SDK = True
except ImportError:
    # Fallback to Old SDK
    try:
        import google.generativeai as genai
        HAS_NEW_SDK = False
    except ImportError:
        print("❌ Neither google.genai (New) nor google.generativeai (Old) is installed.")
        print("   Please run: pip install -U google-generativeai")
        sys.exit(1)

def list_models():
    # Load API Key logic (same as before)
    from config import Config
    api_key = Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY missing.")
        return

    print(f"🔑 Using API Key: {api_key[:5]}...{api_key[-3:]}")
    print(f"📦 SDK Version: {'New (google.genai)' if HAS_NEW_SDK else 'Old (google.generativeai)'}")

    try:
        print("\n📡 Fetching available models...")
        print("="*60)
        
        if HAS_NEW_SDK:
            # New SDK Logic
            client = genai.Client(api_key=api_key)
            for m in client.models.list():
                if 'gemini' in m.name.lower():
                     print(f"Model ID: {m.name}")
                     print(f"  - Display Name: {getattr(m, 'display_name', 'N/A')}")
                     print(f"  - Input Limit: {getattr(m, 'input_token_limit', 'Unknown')}")
                     print(f"  - Output Limit: {getattr(m, 'output_token_limit', 'Unknown')}")
                     print("-" * 60)
        else:
            # Old SDK Logic
            genai.configure(api_key=api_key)
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name.lower():
                    print(f"Model ID: {m.name}")
                    print(f"  - Display Name: {m.display_name}")
                    print(f"  - Input Limit: {m.input_token_limit}")
                    print(f"  - Output Limit: {m.output_token_limit}")
                    print("-" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_models()
