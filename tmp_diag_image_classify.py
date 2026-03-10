"""
診斷：用真實的數學題截圖測試 Qwen3-VL，看模型原始輸出是什麼
"""
import requests, json, re, base64, io
from PIL import Image, ImageDraw, ImageFont

# 製作一張接近真實截圖風格的測試圖（白底黑字，包含中文說明）
img = Image.new('RGB', (500, 120), color='#f8f8f8')
draw = ImageDraw.Draw(img)
draw.rectangle([0, 0, 500, 120], outline='#cccccc', width=2)
draw.text((20, 20), "計算下列各式的值：", fill='#333333')
draw.text((40, 55), "(-36) ÷ (-4) × 3 + 2", fill='#000000')
buf = io.BytesIO()
img.save(buf, format='PNG')
img_b64 = base64.b64encode(buf.getvalue()).decode()

skills = [
    'jh_數學1上_FourArithmeticOperationsOfIntegers',
    'jh_數學1上_FourArithmeticOperationsOfNumbers',
    'jh_數學2上_FourArithmeticOperationsOfPolynomial',
    'jh_數學2上_FourOperationsOfRadicals',
]
skills_str = ', '.join(skills)

prompt_text = f"""
你現在是邏輯辨識核心。請觀察圖片，精確提取數學 LaTeX 算式（需忽略 \\tt 與噪音），並完成技能分類。
【!! 你只能輸出一個 JSON 物件，嚴禁包含任何其他文字、分析過程或 markdown block !!】

【最高指令：技能 ID 選擇】
你『必須』且『只能』從以下清單中選擇一個最符合的作為 skill_id：
{skills_str}

輸出格式要求（skill_id 必須是上面清單中的確切字串）：
{{
  "ocr_text": "12 \\div (-4) \\times (-3)",
  "skill_id": "jh_數學1上_FourArithmeticOperationsOfIntegers",
  "confidence": 95
}}
[嚴格要求] 嚴禁輸出多餘欄位；只輸出 ocr_text、skill_id、confidence。
"""

payload = {
    'model': 'qwen3-vl:8b-instruct-q4_k_m',
    'messages': [{'role': 'user', 'content': prompt_text, 'images': [img_b64]}],
    'stream': False,
    'options': {'temperature': 0.1, 'num_ctx': 4096, 'num_gpu': -1, 'repeat_penalty': 1.05}
}

print('傳送圖片至 Qwen3-VL...')
r = requests.post('http://127.0.0.1:11434/api/chat', json=payload, timeout=120)
r.raise_for_status()
raw_out = r.json().get('message', {}).get('content', '')

print(f'=== 模型原始輸出 ===')
print(repr(raw_out[:2000]))
print()
print(f'=== 原始輸出（可讀）===')
print(raw_out[:2000])
print()

# 模擬後端處理流程
print('=== 模擬後端處理 ===')
# Step 1: 移除 <think>
raw_clean = re.sub(r'<think>.*?</think>', '', raw_out, flags=re.DOTALL).strip()
if not raw_clean:
    raw_clean = raw_out
print(f'移除 <think> 後: {repr(raw_clean[:500])}')

# Step 2: 搜尋 JSON
json_match = re.search(r'(\{.*\})', raw_clean, re.DOTALL)
if json_match:
    candidate = json_match.group(0)
    print(f'找到 JSON 候選: {repr(candidate[:500])}')
    try:
        fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', candidate)
        parsed = json.loads(fixed)
        print(f'解析成功: {parsed}')
    except json.JSONDecodeError as e:
        print(f'JSON 解析失敗: {e}')
        print(f'問題字串: {repr(candidate[:300])}')
else:
    print('找不到 JSON 結構！')
