import sys
sys.path.insert(0, r"E:\Python\MathProject_AST_Research")
from core.healers.live_show_healer import enforce_negative_parentheses
from scripts.evaluate_mcri import evaluate_sympy_verification

# ── Test enforce_negative_parentheses ──────────────────────────────
cases = [
    ("(-4 \\frac{1}{5})",             "(-4\\frac{1}{5})",       "already wrapped mixed  => no change"),
    ("-4 \\frac{1}{5}",               "(-4\\frac{1}{5})",       "bare negative mixed    => wrap all"),
    ("(-3)",                           "(-3)",                   "already wrapped int    => no change"),
    ("-3",                             "(-3)",                   "bare negative int      => wrap"),
    ("(-4 \\frac{1}{5}) + (-3)",      "(-4\\frac{1}{5})+(-3)",  "both already wrapped   => no change"),
    ("(-8 \\frac{7}{10})",            "(-8\\frac{7}{10})",      "Ab2 screenshot case"),
    ("(-3 \\frac{2}{3})",             "(-3\\frac{2}{3})",       "negative 3+2/3 wrapped => no change"),
    ("-3 \\frac{2}{3}",               "(-3\\frac{2}{3})",       "bare negative 3+2/3    => wrap"),
]

print("enforce_negative_parentheses tests:")
print(f"{'Label':<40} {'Expected':<30} {'Got':<30} {'OK?'}")
print("-" * 110)
all_pass = True
for inp, expected, label in cases:
    result, cnt = enforce_negative_parentheses(inp)
    ok = result == expected
    if not ok:
        all_pass = False
    status = "OK" if ok else "FAIL"
    print(f"{label:<40} {expected:<30} {result:<30} {status} (changes={cnt})")

print()
print("ALL PASSED" if all_pass else "SOME FAILED")

# ── Test SymPy verification with new question format ────────────────
print()
print("SymPy verification tests (post-display-fix format):")
sympy_cases = [
    ("計算 $(-4\\frac{1}{5}) + (-9) - (-3\\frac{2}{3}) + (\\frac{-3}{10})$ 的值。", "-59/6", "Ab3 screenshot question"),
    ("計算 $(-2\\frac{3}{4}) + (1\\frac{2}{7})$ 的值。", "-41/28", "Original test question"),
]
print(f"{'Label':<40} {'Score':>6} {'OK?'}")
print("-" * 55)
for q, ans, label in sympy_cases:
    score, note = evaluate_sympy_verification(q, ans)
    ok = score >= 9
    print(f"{label:<40} {score:>6.1f}  {'OK' if ok else 'FAIL'}  ({note})")
