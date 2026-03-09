"""
Verify Fix 1: MCRI syntax score no longer penalises eval inside class bodies.
Verify Fix 2: Ab2 execution code goes through optimize_live_execution_code.
"""
import sys
sys.path.insert(0, r"E:\Python\MathProject_AST_Research")

from scripts.evaluate_mcri import evaluate_live_code

# --- Re-run the real file comparison (Fix 1 check) ---
ab2_file = r"E:\Python\MathProject_AST_Research\generated_scripts\scaler_1773067747_ebdbf2_ab2.py"
ab3_file = r"E:\Python\MathProject_AST_Research\generated_scripts\live_show_1773067748_65a3c4.py"

# Ab2 raw_code = stubs (stub_mode=True, no eval) + generate()
# We simulate by loading the Ab2 file which is just generate()
with open(ab2_file, encoding="utf-8") as f:
    ab2_code_raw = f.read()

# Ab3 healed_exec_code = FULL injected class + generate() (has eval inside IntegerOps)
with open(ab3_file, encoding="utf-8") as f:
    ab3_code_full = f.read()

exec_result_ok = {
    "question_text": "計算 $(2\\frac{2}{3}) + (-2\\frac{1}{2})$ 的值。",
    "answer": "",
    "correct_answer": "1/6",
    "mode": 1,
}

print("=" * 60)
print("Fix 1: MCRI syntax score with injected eval inside class")
print("=" * 60)
ab2_m = evaluate_live_code(code=ab2_code_raw, exec_result=exec_result_ok, healer_trace={}, ablation_mode=False)
ab3_m = evaluate_live_code(code=ab3_code_full, exec_result=exec_result_ok, healer_trace={"regex_fixes": 3, "ast_fixes": 0}, ablation_mode=False)

print(f"{'Metric':<18}  {'Ab2':>8}  {'Ab3':>8}  {'Ab3-Ab2':>8}")
print("-" * 48)
for k in ["syntax_score", "logic_score", "render_score", "stability_score", "total_score"]:
    diff = ab3_m[k] - ab2_m[k]
    print(f"{k:<18}  {ab2_m[k]:>8}  {ab3_m[k]:>8}  {diff:>+8.1f}")
print()
print(f"Ab2 l1_syntax={ab2_m['breakdown']['l1_syntax']}  (expect 7.5 = no forbidden eval)")
print(f"Ab3 l1_syntax={ab3_m['breakdown']['l1_syntax']}  (expect 7.5 = eval inside class ignored)")
print(f"Ab3 - Ab2 total = {ab3_m['total_score'] - ab2_m['total_score']:+.1f}  (expect >= 0)")

# --- Fix 2: optimize_live_execution_code is now applied to Ab2 ---
print()
print("=" * 60)
print("Fix 2: optimize_live_execution_code applied to Ab2 code")
print("=" * 60)
from core.routes.live_show import _optimize_live_execution_code

test_code_with_big_range = """
def generate(level=1, **kwargs):
    for _ in range(1000):
        import random
        return {"question_text": "test", "answer": "", "correct_answer": "1", "mode": 1}
"""
optimized = _optimize_live_execution_code(test_code_with_big_range)
print("Input:  range(1000)")
print(f"Output: {'range(120)' if 'range(120)' in optimized else 'range(1000) — NOT optimized!'}")
assert "range(120)" in optimized, "optimize should cap range(1000) to range(120)"
print("OK — Ab2 will now also have range loops capped, CPU time is fair")
