import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Pre-check API Key to avoid app.py initialization crash
if not os.environ.get("GEMINI_API_KEY"):
    print("⚠️ GEMINI_API_KEY not found in env. Setting dummy key to bypass app init crash.")
    os.environ["GEMINI_API_KEY"] = "dummy_key_for_local_test"

from core.code_generator import auto_generate_skill_code
from config import Config
from app import app

if __name__ == "__main__":
    # Parse command line argument
    if len(sys.argv) > 1:
        skill_id = sys.argv[1]
    else:
        skill_id = "jh_數學1上_MixedIntegerAdditionAndSubtraction"
    
    print(f"🚀 Starting Research Quick Fix for {skill_id}...")
    print(f"🔧 Model: {Config.MODEL_ROLES['coder']['model']}")
    
    with app.app_context():
        try:
            # ablation_id=3 represents "Self-Healing"
            result = auto_generate_skill_code(skill_id, ablation_id=3) 
            print("✅ Generation Function Returned.")
        except Exception as e:
            print(f"❌ Generation Failed: {e}")
            import traceback
            traceback.print_exc()
