import sys
import json
import ast
sys.path.append('.')
from scripts.evaluate_mcri import evaluate_live_code

# Mock the result from scaler.py
# Pretend it generated a perfect code block
code = """
def generate(level=1):
    def check(ans):
        return ans == "5"
    return "What is 2+3?", "5", "5"
"""

exe_result = {
    "question_text": "What is 2+3?",
    "answer": "5",
    "correct_answer": "5"
}

ab3_mcri = evaluate_live_code(
    code=code,
    exec_result=exe_result,
    healer_trace={"regex_fixes": 0, "ast_fixes": 0},
    ablation_mode=False
)

ab2_mcri = evaluate_live_code(
    code=code,
    exec_result=exe_result,
    healer_trace={},
    ablation_mode=False
)

print(f"Ab3 Score: {ab3_mcri['total_score']}")
print(f"Ab2 Score: {ab2_mcri['total_score']}")
print(f"Ab3 Breakdown: {json.dumps(ab3_mcri['breakdown'], indent=2)}")
print(f"Ab2 Breakdown: {json.dumps(ab2_mcri['breakdown'], indent=2)}")

