"""Bug 21 Fix 驗證：greedy JSON regex → raw_decode scan"""
import re, json

_json_decoder = json.JSONDecoder()

def extract_classify_json(raw_out_clean):
    parsed_res = None
    for _scan_m in re.finditer(r'\{', raw_out_clean):
        _snip = raw_out_clean[_scan_m.start():]
        _snip_fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', _snip)
        _snip_fixed = re.sub(r'\s*//[^\n"]*', '', _snip_fixed)
        try:
            _obj, _ = _json_decoder.raw_decode(_snip_fixed)
            if isinstance(_obj, dict) and ('ocr_text' in _obj or 'skill_id' in _obj):
                parsed_res = _obj
                break
        except (json.JSONDecodeError, ValueError):
            continue
    return parsed_res

# REAL_JSON 模擬 Ollama response.json()["message"]["content"] 的實際 Python 字串：
# Ollama 已解碼外層 JSON，所以 content 裡的 \div 是一個反斜線（非 \\div）
REAL_JSON = '{"ocr_text": "12 \\div (-4) \\times (-3)", "skill_id": "jh_Test", "confidence": 95}'

cases = [
    ("情境 1 - 正常 JSON", REAL_JSON),
    ("情境 2 - 說明文字 + { } 在 JSON 前", 'Result: {math info}. Answer:\n' + REAL_JSON),
    ("情境 3 - 多行 JSON（正常）", '{\n  "ocr_text": "12+3",\n  "skill_id": "xxx",\n  "confidence": 90\n}'),
    ("情境 4 - think block 之後", '<think>fake: {"a":"b"}</think>\n' + REAL_JSON),
    ("情境 5 - LaTeX \\frac 在 ocr_text 中", '{"ocr_text": "\\\\frac{1}{2} + 3", "skill_id": "jh_Test", "confidence": 95}'),
    ("情境 6 - 舊 greedy 失敗案例", '{fake stuff here} more text ' + REAL_JSON),
]

all_pass = True
for name, text in cases:
    # Remove think blocks first (same as production code)
    clean = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    clean = re.sub(r'<think>.*', '', clean, flags=re.DOTALL)
    clean = clean.strip() or text

    result = extract_classify_json(clean)
    if result and ('ocr_text' in result or 'skill_id' in result):
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name} → FAILED (result={result})")
        all_pass = False

# 舊 greedy 方式測試（應該在情境 2/6 失敗）
print("\n--- 舊 greedy regex 結果（Bug 21 前）---")
for name, text in cases:
    clean = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    clean = re.sub(r'<think>.*', '', clean, flags=re.DOTALL)
    clean = clean.strip() or text

    m = re.search(r'(\{.*\})', clean, re.DOTALL)
    if m:
        try:
            fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', m.group(0))
            obj = json.loads(fixed)
            if isinstance(obj, dict) and ('ocr_text' in obj or 'skill_id' in obj):
                print(f"  ✅ {name}")
                continue
        except json.JSONDecodeError:
            pass
    print(f"  ❌ {name} → FAILED")

print(f"\n{'✅ ALL PASS' if all_pass else '❌ SOME FAILED'} (Bug 21 scan approach)")
