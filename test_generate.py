import sys
import os
import json
from flask import Flask, request

# add project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.routes.live_show import generate_live

app = Flask(__name__)

payload = {
    "prompt": "計算 1+1",
    "ablation_mode": False,
    "count": 1,
    "model_id": "qwen3-8b",
    "master_spec": "【2. 目標 DNA 與邏輯食譜 (MASTER_SPEC)】\n1. 邏輯塊與符號隨機化: \nop = random.choice(['+', '-', '*', '/'])"
}

with app.test_request_context(json=payload):
    try:
        res = generate_live()
        data = res[0].get_json() if isinstance(res, tuple) else res.get_json()
        with open("test_generate_out.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        import traceback
        with open("test_generate_out.json", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
