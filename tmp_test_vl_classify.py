import requests, json, re

skills = ["jh_數學1上_FourArithmeticOperationsOfIntegers", "jh_數學1上_FourArithmeticOperationsOfNumbers"]
skills_str = ", ".join(skills)

prompt_text = f"""
你現在是邏輯辨識核心。請閱讀以下使用者提供的數學算式或指令，精確完成技能分類。
【!! 你只能輸出一個 JSON 物件，嚴禁包含任何其他文字、分析過程或 markdown block !!】

【使用者輸入文字】
12 ÷ (-4) × (-3)

【最高指令：技能 ID 選擇】
你『必須』且『只能』從以下清單中選擇一個最符合的作為 skill_id：
{skills_str}

輸出格式要求（skill_id 必須是上面清單中的確切字串）：
{{
  "ocr_text": "12 ÷ (-4) × (-3)",
  "skill_id": "jh_數學1上_FourArithmeticOperationsOfIntegers",
  "confidence": 95
}}
[嚴格要求] 嚴禁輸出多餘欄位；只輸出 ocr_text、skill_id、confidence。
"""

payload = {
    "model": "qwen3-vl:8b-instruct-q4_k_m",
    "messages": [{"role": "user", "content": prompt_text}],
    "stream": False,
    "options": {
        "temperature": 0.1,
        "num_ctx": 4096,
        "num_gpu": -1,
        "repeat_penalty": 1.05
    }
}

print("Sending request...")
r = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=120)
r.raise_for_status()
result = r.json()
raw_out = result.get("message", {}).get("content", "")
print(f"RAW OUTPUT (repr): {repr(raw_out[:1000])}")
print("---")
print(f"RAW OUTPUT: {raw_out[:1000]}")

# Test JSON extraction
json_match = re.search(r'(\{.*\})', raw_out, re.DOTALL)
if json_match:
    clean = json_match.group(0)
    print(f"\nExtracted JSON string: {repr(clean[:500])}")
    try:
        clean2 = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', clean)
        parsed = json.loads(clean2)
        print(f"Parsed JSON: {parsed}")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"After escape fix: {repr(clean2[:500])}")
else:
    print("No JSON found in output!")
