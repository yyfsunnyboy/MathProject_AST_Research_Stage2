import sys
sys.path.insert(0, '.')
from scripts.evaluate_mcri import evaluate_live_code

with open('generated_scripts/live_show_1773070081_7e160c.py', encoding='utf-8') as f:
    code = f.read()

result = evaluate_live_code(
    code=code,
    exec_result={'question_text': 'test', 'answer': '1/2', 'correct_answer': '1/2', 'mode': 1},
    healer_trace={'regex_fixes': 0, 'ast_fixes': 0},
    ablation_mode=False,
)
bd = result['breakdown']
print("l1_syntax =", bd['l1_syntax'])
print("syntax_score =", result['syntax_score'])
print("total =", result['total_score'])
