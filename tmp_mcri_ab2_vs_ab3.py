"""Diagnostic: compare Ab2 vs Ab3 MCRI scoring side by side."""
import sys
sys.path.insert(0, r"E:\Python\MathProject_AST_Research")

from scripts.evaluate_mcri import evaluate_live_code, analyze_code_robustness

# Simulate typical scaffold code (api_stubs + generated code with safe_eval + check fn)
BASE_CODE = """
class IntegerOps:
    @staticmethod
    def random_nonzero(a, b):
        import random
        return random.choice([x for x in range(a, b+1) if x != 0])

class FractionOps:
    @staticmethod
    def to_latex(val, mixed=False):
        return str(val)

def safe_eval(expr, context=None):
    from fractions import Fraction
    import math
    return eval(expr)

def generate(level=1, **kwargs):
    for _ in range(100):
        try:
            a = IntegerOps.random_nonzero(-10, 10)
            b = IntegerOps.random_nonzero(-10, 10)
            result = safe_eval(f"abs({a}) + abs({b})")
            if result < 0:
                continue
            return {
                'question_text': f'計算 $|{a}| + |{b}|$ 的值。',
                'answer': '',
                'correct_answer': str(result),
                'mode': 1,
                '_o1_healed': False
            }
        except Exception:
            continue
    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    return {'is_correct': str(user_answer).strip() == str(correct_answer).strip()}
"""

exec_result = {
    'question_text': '計算 $|3| + |4|$ 的值。',
    'answer': '',
    'correct_answer': '7',
    'mode': 1
}

# Ab2: no healer trace
ab2_mcri = evaluate_live_code(
    code=BASE_CODE,
    exec_result=exec_result,
    healer_trace={},
    ablation_mode=False
)

# Ab3-scenario A: healer_trace with regex_fixes=3, ast_fixes=1 (current, includes fake safe_eval fix)
ab3_mcri_with_fake = evaluate_live_code(
    code=BASE_CODE,
    exec_result=exec_result,
    healer_trace={"regex_fixes": 3, "ast_fixes": 1},
    ablation_mode=False
)

# Ab3-scenario B: after fix — ast_fixes=0 (safe_eval removed from target_funcs)
ab3_mcri_no_fake = evaluate_live_code(
    code=BASE_CODE,
    exec_result=exec_result,
    healer_trace={"regex_fixes": 3, "ast_fixes": 0},
    ablation_mode=False
)

print("=" * 60)
print(f"{'Metric':<18}  {'Ab2':>8}  {'Ab3(now)':>10}  {'Ab3(fixed)':>12}")
print("=" * 60)
for key in ["syntax_score", "logic_score", "render_score", "stability_score", "total_score"]:
    print(f"{key:<18}  {ab2_mcri[key]:>8}  {ab3_mcri_with_fake[key]:>10}  {ab3_mcri_no_fake[key]:>12}")
print("=" * 60)
print(f"{'robust_status':<18}  {ab2_mcri['breakdown']['l5_robust_status']:>8}  "
      f"{ab3_mcri_with_fake['breakdown']['l5_robust_status']:>10}  "
      f"{ab3_mcri_no_fake['breakdown']['l5_robust_status']:>12}")
print(f"{'total_fixes':<18}  {ab2_mcri['breakdown']['healer_fixes']:>8}  "
      f"{ab3_mcri_with_fake['breakdown']['healer_fixes']:>10}  "
      f"{ab3_mcri_no_fake['breakdown']['healer_fixes']:>12}")
print()
print(f"Ab3(now)-Ab2   = {round(ab3_mcri_with_fake['total_score'] - ab2_mcri['total_score'], 2):+.2f}")
print(f"Ab3(fixed)-Ab2 = {round(ab3_mcri_no_fake['total_score'] - ab2_mcri['total_score'], 2):+.2f}")

# Also show the robustness of BASE_CODE
status, evidence = analyze_code_robustness(BASE_CODE)
print(f"\nanalyze_code_robustness: status={status}, evidence={evidence}")
