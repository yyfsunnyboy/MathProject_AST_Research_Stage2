import requests, json, re, base64, io
from PIL import Image, ImageDraw

# Create a simple test image with math text
img = Image.new('RGB', (300, 100), color='white')
draw = ImageDraw.Draw(img)
draw.text((10, 30), '12 / (-4) x (-3)', fill='black')
buf = io.BytesIO()
img.save(buf, format='PNG')
img_b64 = base64.b64encode(buf.getvalue()).decode()

skills = ['jh_數學1上_FourArithmeticOperationsOfIntegers', 'jh_數學1上_FourArithmeticOperationsOfNumbers']
skills_str = ', '.join(skills)

prompt_text = f"""
你現在是邏輯辨識核心。請觀察圖片，精確提取數學算式，並完成技能分類。
【!! 你只能輸出一個 JSON 物件，嚴禁包含任何其他文字 !!】

【技能清單】
{skills_str}

請輸出：
{{
  "ocr_text": "提取到的算式",
  "skill_id": "清單中的技能ID",
  "confidence": 95
}}
"""

payload = {
    'model': 'qwen3-vl:8b-instruct-q4_k_m',
    'messages': [{'role': 'user', 'content': prompt_text, 'images': [img_b64]}],
    'stream': False,
    'options': {'temperature': 0.1, 'num_ctx': 4096}
}

print('Sending image test request...')
r = requests.post('http://127.0.0.1:11434/api/chat', json=payload, timeout=120)
r.raise_for_status()
result = r.json()
raw = result.get('message', {}).get('content', '')
print(f'STATUS: {r.status_code}')
print(f'RAW OUTPUT (repr): {repr(raw[:3000])}')
print('---')
print(f'RAW OUTPUT:\n{raw[:3000]}')

# Try JSON extraction
json_match = re.search(r'(\{.*\})', raw, re.DOTALL)
if json_match:
    clean = json_match.group(0)
    print(f'\nJSON match found: {repr(clean[:500])}')
    try:
        clean2 = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', clean)
        parsed = json.loads(clean2)
        print(f'Parsed: {parsed}')
    except json.JSONDecodeError as e:
        print(f'JSON parse error: {e}')
else:
    print('\nNo JSON found in output!')
