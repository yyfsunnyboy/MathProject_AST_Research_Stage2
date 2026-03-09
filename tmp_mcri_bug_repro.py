# -*- coding: utf-8 -*-
"""Reproduce and fix the Ab3 < Ab2 MCRI bug."""
import sys
sys.path.insert(0, r'D:\Python\MathProject_AST_Research')
from scripts.evaluate_mcri import evaluate_live_code, analyze_code_robustness

exec_result = {
    'question_text': '计算 $x$ 的值。',
    'answer': '',
    'correct_answer': '38/15',
    'mode': 1
}

# Case 1: Code WITH safe_eval (both ROBUST)
code_with_safe_eval = r'''
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    for _ in range(100):
        try:
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            eval_str = f"Fraction({n1}, {d1})"
            ans = safe_eval(eval_str)
            if not isinstance(ans, Fraction):
                continue
            return {"question_text": "计算 $x$", "answer": "", "correct_answer": str(ans)}
        except Exception:
            continue
    return {"question_text": "Error", "answer": "", "correct_answer": "0"}

def check(u, c):
    try:
        return {"correct": bool(u == c), "result": "OK"}
    except:
        return {"correct": False, "result": "NO"}
'''

# Case 2: Code WITHOUT safe_eval (Qwen sometimes generates direct Fraction arithmetic)
code_no_safe_eval = r'''
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    for _ in range(100):
        try:
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            ans = Fraction(n1, d1)
            if not isinstance(ans, Fraction):
                continue
            return {"question_text": "计算 $x$", "answer": "", "correct_answer": str(ans)}
        except Exception:
            continue
    return {"question_text": "Error", "answer": "", "correct_answer": "0"}

def check(u, c):
    try:
        return {"correct": bool(u == c), "result": "OK"}
    except:
        return {"correct": False, "result": "NO"}
'''

stubs = '''
class IntegerOps:
    @staticmethod
    def random_nonzero(min_val, max_val): ...
class FractionOps:
    @staticmethod
    def to_latex(val, mixed=False): ...
'''

ab2_code_with_stubs = stubs + code_with_safe_eval
ab2_code_no_safe_eval_with_stubs = stubs + code_no_safe_eval

print('='*60)
print('CASE 1: Qwen uses safe_eval (correct pattern)')
print('='*60)
r_ab3 = analyze_code_robustness(code_with_safe_eval)
r_ab2 = analyze_code_robustness(ab2_code_with_stubs)
print(f'Ab3 robustness: {r_ab3[0]} | Ab2 robustness: {r_ab2[0]}')
m3 = evaluate_live_code(code=code_with_safe_eval, exec_result=exec_result, healer_trace={'regex_fixes': 2, 'ast_fixes': 1}, ablation_mode=False)
m2 = evaluate_live_code(code=ab2_code_with_stubs, exec_result=exec_result, healer_trace={}, ablation_mode=False)
print(f'Ab3 stability={m3["stability_score"]}  total={m3["total_score"]}')
print(f'Ab2 stability={m2["stability_score"]}  total={m2["total_score"]}')
ok = m3["total_score"] >= m2["total_score"]
print(f'{"OK: Ab3>=Ab2" if ok else "BUG: Ab3<Ab2"}')

print()
print('='*60)
print('CASE 2: Qwen uses direct Fraction() — no safe_eval (BUG case)')
print('='*60)
r_ab3b = analyze_code_robustness(code_no_safe_eval)
r_ab2b = analyze_code_robustness(ab2_code_no_safe_eval_with_stubs)
print(f'Ab3 robustness: {r_ab3b[0]} | Ab2 robustness: {r_ab2b[0]}')
m3b = evaluate_live_code(code=code_no_safe_eval, exec_result=exec_result, healer_trace={'regex_fixes': 2, 'ast_fixes': 1}, ablation_mode=False)
m2b = evaluate_live_code(code=ab2_code_no_safe_eval_with_stubs, exec_result=exec_result, healer_trace={}, ablation_mode=False)
print(f'Ab3 stability={m3b["stability_score"]}  total={m3b["total_score"]}')
print(f'Ab2 stability={m2b["stability_score"]}  total={m2b["total_score"]}')
ok2 = m3b["total_score"] >= m2b["total_score"]
print(f'{"OK: Ab3>=Ab2" if ok2 else "BUG CONFIRMED: Ab3<Ab2  <-- This is why!"}')
print()
print(f'Gap: Ab2={m2b["total_score"]} Ab3={m3b["total_score"]}  Ab3-Ab2={m3b["total_score"]-m2b["total_score"]:+.1f}')

print()
print('='*60)
print('CASE 3 (FIX 2): Ab3 evaluated WITH api_stubs (structural fix)')
print('='*60)
# After Fix 2: run_ab3_full_healer now passes api_stubs + healed_exec_code to evaluate_live_code
ab3_code_with_stubs_fix2 = stubs + code_no_safe_eval
r_ab3c = analyze_code_robustness(ab3_code_with_stubs_fix2)
r_ab2c = analyze_code_robustness(ab2_code_no_safe_eval_with_stubs)
print(f'Ab3 robustness: {r_ab3c[0]} | Ab2 robustness: {r_ab2c[0]}')
m3c = evaluate_live_code(code=ab3_code_with_stubs_fix2, exec_result=exec_result, healer_trace={'regex_fixes': 2, 'ast_fixes': 1}, ablation_mode=False)
m2c = evaluate_live_code(code=ab2_code_no_safe_eval_with_stubs, exec_result=exec_result, healer_trace={}, ablation_mode=False)
print(f'Ab3 stability={m3c["stability_score"]}  total={m3c["total_score"]}')
print(f'Ab2 stability={m2c["stability_score"]}  total={m2c["total_score"]}')
ok3 = m3c["total_score"] >= m2c["total_score"]
print(f'{"OK: Ab3>=Ab2 (Fix 2 works!)" if ok3 else "STILL BROKEN"}')
print(f'Gap: Ab3-Ab2={m3c["total_score"]-m2c["total_score"]:+.1f}')
