"""Bug 22 Fix 驗證：\\div (已正確 JSON 逃逸) 不應被二次逃逸"""
import re, json

def scan_json(raw_out_clean):
    _json_decoder = json.JSONDecoder()
    parsed_res = None
    for _scan_m in re.finditer(r'\{', raw_out_clean):
        _snip = raw_out_clean[_scan_m.start():]
        # Bug 22 fix: (?<!\\) lookbehind
        _snip_fixed = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', _snip)
        _snip_fixed = re.sub(r'\s*//[^\n"]*', '', _snip_fixed)
        try:
            _obj, _ = _json_decoder.raw_decode(_snip_fixed)
            if isinstance(_obj, dict) and ('ocr_text' in _obj or 'skill_id' in _obj):
                parsed_res = _obj
                break
        except (json.JSONDecodeError, ValueError):
            continue
    return parsed_res

def scan_json_old(raw_out_clean):
    """舊的 Bug 17 fix（沒有 lookbehind）"""
    _json_decoder = json.JSONDecoder()
    for _scan_m in re.finditer(r'\{', raw_out_clean):
        _snip = raw_out_clean[_scan_m.start():]
        _snip_fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', _snip)
        _snip_fixed = re.sub(r'\s*//[^\n"]*', '', _snip_fixed)
        try:
            _obj, _ = _json_decoder.raw_decode(_snip_fixed)
            if isinstance(_obj, dict) and ('ocr_text' in _obj or 'skill_id' in _obj):
                return _obj
        except (json.JSONDecodeError, ValueError):
            continue
    return None

# 這就是 Flask terminal 印出的實際 raw_out_clean（repr 顯示 \\\\div = 實際 \\div）
actual_raw = '{\n  "ocr_text": "5 \\\\times 12 - 30 \\\\div (-5)",\n  "skill_id": "jh_\u6578\u5b8c1\u4e0a_FourArithmeticOperationsOfIntegers",\n  "confidence": 95\n}'
print(f"actual_raw: {repr(actual_raw)}")

cases = [
    ("實際 Qwen3-VL 輸出（\\\\div 已逃逸）", actual_raw),
    ("模型輸出裸 \\div（未逃逸）", '{"ocr_text": "5 \\times 12 - 30 \\div (-5)", "skill_id": "jh_Test", "confidence": 95}'),
]

print("\n--- 新 scan (Bug 22 fix) ---")
for name, text in cases:
    result = scan_json(text)
    if result:
        print(f"  ✅ {name} → ocr_text={result.get('ocr_text')}")
    else:
        print(f"  ❌ {name} → FAILED")

print("\n--- 舊 scan (Bug 22 前) ---")
for name, text in cases:
    result = scan_json_old(text)
    if result:
        print(f"  ✅ {name} → ocr_text={result.get('ocr_text')}")
    else:
        print(f"  ❌ {name} → FAILED")
