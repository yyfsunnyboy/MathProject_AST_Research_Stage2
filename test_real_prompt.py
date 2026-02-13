
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

# FORCE USE NEW SDK for reproduction
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ google.genai (New SDK) not found. Cannot reproduce issue.")
    sys.exit(1)

api_key = Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ API Key missing")
    sys.exit(1)

print(f"✅ Using API Key: {api_key[:5]}...")

client = genai.Client(api_key=api_key)

# The Exact Prompt from Ab1 file
PROMPT = """【角色設定】
你是一位中學數學老師的「出題助理」。

【任務說明】
請幫我寫一個 Python 程式，用來自動生成數學題目。
★ 題目主題是：「整數四則運算」（包含括號、絕對值、運算優先級）
這個程式需要隨機產生數字，每次執行都能變換數值。
請使用跟課本一樣的格式表達數學式子。

【參考例題】
以下是我們想模仿的題目類型（請參考這個邏輯來寫程式）：
範例：計算 `[(-20)+(-10)]÷(-5)×3+|8×(-2)-5|`的值。的值。
答案：-6

【程式要求】
1. 請寫成兩個函式：
   - `def generate(level=1, **kwargs)`: 生成題目
   - `def check(user_answer, correct_answer)`: 檢查答案是否正確

2. `generate` 函式要回傳一個字典 (Dictionary)，包含以下欄位（請照抄 key 名稱）：
   - 'question_text': 題目文字
   - 'answer': 空字串 ''
   - 'correct_answer': 正確答案（必須是字串，例如："24" 或 "3x^2+5"；多個答案用逗號分隔）
   - 'mode': 1

3. `check` 函式請回傳一個字典，包含：
   - 'correct': True 或 False
   - 'result': 回傳 '正確' 或 '錯誤'

4. 請使用 Python 的 standard library (如 random, math) 即可。
   - 🔴 重要：不要使用 sympy、numpy 或其他外部套件

⚠️ 重要：只輸出 Python 程式碼！
- ✅ 正確：直接從 import 開始寫
- ❌ 錯誤：不要加任何說明文字或註解在程式碼之外
- ❌ 錯誤：不要在程式碼後面加「這個程式碼會...」的說明
- ❌ 錯誤：不要在程式碼後面加英文說明（如 "This code defines..."）
- ❌ 錯誤：不要用 ```python 包裹代碼
- ❌ 錯誤：不要加 Example usage 或 `if __name__ == '__main__'`
- ❌ 錯誤：不要加 Explanation/說明段落
- 🔴 CRITICAL：程式碼結束後不可有任何文字（包括空白行後的說明）
"""

# Reconstruct Safety Settings from Config
safety_settings_dicts = Config.CODER_PRESETS['gemini-2.5-flash']['safety_settings']
converted_safety = []
# Try to be robust: check if dicts work directly or need types
# Test Case 1: Use types.SafetySetting (The "Official" way)
for s in safety_settings_dicts:
    converted_safety.append(
        types.SafetySetting(
            category=s['category'],
            threshold=s['threshold']
        )
    )

# Use dictionary config construction (New SDK style)
config_params = {
    "temperature": 0.1,
    "max_output_tokens": 8192,
    "safety_settings": converted_safety
}

print(f"\n=== Testing Real Prompt with New SDK (gemini-2.5-flash) ===")
print(f"Config: {config_params}")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=PROMPT,
        config=config_params # Dictionary config, containing types objects
    )
    
    txt = response.text
    print(f"\nResponse Length: {len(txt)}")
    print(f"Token Count (approx): {len(txt)//4}")
    
    if hasattr(response, 'candidates') and response.candidates:
        cand = response.candidates[0]
        print(f"Finish Reason: {cand.finish_reason}")
    
    print("\n--- Last 200 chars ---")
    print(txt[-200:])

except Exception as e:
    print(f"\n❌ Error: {e}")
