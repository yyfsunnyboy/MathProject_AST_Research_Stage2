import json
import requests

BASE = "http://127.0.0.1:5000"
cases = [
    "計算 (-2 1/6)+1 2/9-(-1 1/3) 的值。",
    "計算 (-2 3/4)+1 2/7 的值。",
    "計算 | 8×(-2)-5 | ÷ 7×(-3) 的值。",
    "計算 (3/5-7/10)+(-2/3) 的值。",
    "計算 (-4 1/2)÷(1 1/5)+3/10 的值。",
]

for i, text in enumerate(cases, 1):
    c = requests.post(f"{BASE}/api/classify", json={"text_data": text}, timeout=120)
    c.raise_for_status()
    cobj = c.json()
    skill_id = cobj.get("skill_id")

    payload = {
        "prompt": text,
        "ablation_mode": False,
        "model_id": "qwen3-8b",
        "skill_id": skill_id,
    }
    g = requests.post(f"{BASE}/api/generate_live", json=payload, timeout=180)
    g.raise_for_status()
    obj = g.json()

    final_code = obj.get("final_code", "") or ""
    has_generate = "def generate(" in final_code
    ab2 = obj.get("ab2_result") or {}

    print(f"CASE#{i}")
    print(f"input={text}")
    print(f"success={obj.get('success')} route={obj.get('route_mode')}")
    print(f"ab3_error={obj.get('error', '')}")
    print(f"ab2_error={ab2.get('error', '')}")
    print(f"ab3_has_generate={has_generate}")
    print(f"eq_raw={ab2.get('raw_code') == obj.get('raw_code')}")
    print(f"ab2_problem={(ab2.get('problem') or '').replace(chr(10), ' ')}")
    print(f"ab3_problem={(obj.get('problem') or '').replace(chr(10), ' ')}")
    print()
