import os
import sys

# Add project root needed for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.ai_wrapper import get_ai_client

def test_gemini():
    print("Testing gemini-2.5-flash...")
    try:
        # Override config temporarily
        Config.MODEL_ROLES['default'] = {
            'provider': 'google',
            'model': 'gemini-2.5-flash',
            'temperature': 0.1,
            'max_tokens': 100
        }
        client = get_ai_client('default')
        res = client.generate_content("Hello, write a 1 line greeting")
        print("Success 2.5:", res.text)
    except Exception as e:
        print("Error 2.5:", e)

    print("\nTesting gemini-3-flash-preview...")
    try:
        # Override config temporarily
        Config.MODEL_ROLES['default'] = {
            'provider': 'google',
            'model': 'gemini-3-flash-preview',
            'temperature': 0.1,
            'max_tokens': 100
        }
        client = get_ai_client('default')
        res = client.generate_content("Hello, write a 1 line greeting")
        print("Success 3.0:", res.text)
    except Exception as e:
        print("Error 3.0:", e)

if __name__ == "__main__":
    test_gemini()
