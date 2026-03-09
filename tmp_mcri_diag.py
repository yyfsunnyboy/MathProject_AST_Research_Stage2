# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\Python\MathProject_AST_Research')
from scripts.evaluate_mcri import evaluate_live_code, analyze_code_robustness

# Healed Qwen code WITHOUT stubs (what healed_exec_code looks like for Ab3)
ab3_code = r'''
import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    for _ in range(100):
        try:
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(2, 10)
            eval_str = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2})"
            ans = safe_eval(eval_str)
            if not isinstance(ans, Fraction) or abs(ans.numerator) > 120 or ans.denominator > 120:
                continue
            f1_str = FractionOps.to_latex(Fraction(n1, d1), mixed=True)
            f2_str = FractionOps.to_latex(Fraction(n2, d2), mixed=True)
            math_str = f"({f1_str}) + ({f2_str})"
            correct_answer = str(ans.numerator) if ans.denominator == 1 else f"{ans.numerator}/{ans.denominator}"
            return {"question_text": "计算 $" + math_str + "$ 的值。", "answer": "", "correct_answer": correct_answer, "mode": 1}
        except Exception:
            continue
    return {"question_text": "Error", "answer": "", "correct_answer": "0", "mode": 1}

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {"correct": True, "result": "正确"}
        from fractions import Fraction
        if Fraction(ua) == Fraction(ca):
            return {"correct": True, "result": "正确"}
    except Exception:
        pass
    return {"correct": False, "result": "错误"}
'''

# Ab2 code = stubs (stub_mode=True, bodies=...) + same Qwen code
stubs_prefix = '''
class IntegerOps:
    @staticmethod
    def random_nonzero(min_val, max_val): ...
    @staticmethod
    def safe_eval(expr): ...

class FractionOps:
    @staticmethod
    def to_latex(val, mixed=False): ...
'''

ab2_code = stubs_prefix + ab3_code

exec_result = {
    'question_text': '\u8ba1\u7b97 $' + r'(1 \frac{1}{3}) + (2 \frac{1}{5})' + '$ \u7684\u5024\u3002',
    'answer': '',
    'correct_answer': '38/15',
    'mode': 1
}

# --- Also test the bug case: Ab3 code WITHOUT safe_eval ---
print('\n=== BUG CASE: Ab3 code without safe_eval (Qwen sometimes does this) ===')
ab3_no_safe_eval = ab3_code.replace(
    '    eval_str = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2})"\n            ans = safe_eval(eval_str)',
    '    ans = Fraction(n1, d1) + Fraction(n2, d2)'
).replace('            eval_str = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2})"\n            ans = safe_eval(eval_str)', '            ans = Fraction(n1, d1) + Fraction(n2, d2)'
)

print('=== Ab3 code (WITHOUT stubs) — healed_exec_code ===')
robust_ab3, reason_ab3 = analyze_code_robustness(ab3_code)
print(f'  robust_status: {robust_ab3} | reason: {reason_ab3}')
mcri_ab3_fix = evaluate_live_code(code=ab3_code, exec_result=exec_result,
    healer_trace={'regex_fixes': 2, 'ast_fixes': 1}, ablation_mode=False)
mcri_ab3_nofix = evaluate_live_code(code=ab3_code, exec_result=exec_result,
    healer_trace={}, ablation_mode=False)
print(f'  With fixes (regex=2,ast=1): stability={mcri_ab3_fix["stability_score"]}  total={mcri_ab3_fix["total_score"]}')
print(f'  No  fixes:                  stability={mcri_ab3_nofix["stability_score"]}  total={mcri_ab3_nofix["total_score"]}')

print()
print('=== Ab2 code (WITH stubs) — raw_code = api_stubs + final_code ===')
robust_ab2, reason_ab2 = analyze_code_robustness(ab2_code)
print(f'  robust_status: {robust_ab2} | reason: {reason_ab2}')
mcri_ab2 = evaluate_live_code(code=ab2_code, exec_result=exec_result,
    healer_trace={}, ablation_mode=False)
print(f'  No fixes (Ab2 no healer):   stability={mcri_ab2["stability_score"]}  total={mcri_ab2["total_score"]}')

print()
print('=== VERDICT ===')
print(f'Ab3 total (with healer fixes) = {mcri_ab3_fix["total_score"]}')
print(f'Ab2 total (no healer)         = {mcri_ab2["total_score"]}')
if mcri_ab3_fix["total_score"] < mcri_ab2["total_score"]:
    print('BUG CONFIRMED: Ab3 < Ab2 even with healer fixes!')
else:
    print('OK: Ab3 >= Ab2')
