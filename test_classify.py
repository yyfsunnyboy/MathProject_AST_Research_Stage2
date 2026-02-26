import sys
import os

# add project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.routes.live_show import classify_input
from flask import Flask, jsonify

app = Flask(__name__)

with app.test_request_context(json={"text_data": "一元一次方程式的應用問題"}):
    try:
        res = classify_input()
        print("Success:")
        print(res.get_json())
    except Exception as e:
        import traceback
        print("Error Server Crash:", traceback.format_exc())
