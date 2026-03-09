import sys
sys.path.insert(0, r"E:\Python\MathProject_AST_Research")
from scripts.evaluate_mcri import evaluate_sympy_verification

test_cases = [
    ("計算 $(-2 \\frac{3}{4}) + (1 \\frac{2}{7})$ 的值。", "-41/28", "OCR 題目 -2·3/4 + 1·2/7（帶空格）"),
    ("計算 $(-2\\frac{3}{4}) + (1\\frac{2}{7})$ 的值。",  "-41/28", "無空格版"),
    ("計算 $(1 \\frac{1}{5}) + (1 \\frac{1}{6})$ 的值。", "71/30",  "正數帶分數"),
    ("計算 $\\frac{13}{4} + \\frac{5}{3}$ 的值。",        "59/12",  "純假分數（原本就可以）"),
    ("計算 $(-3) + (5)$ 的值。",                          "2",      "整數題"),
]
print(f"{'Label':<38} {'Score':>6} {'OK?':>5}  Note")
print("-" * 70)
for q, ans, label in test_cases:
    score, note = evaluate_sympy_verification(q, ans)
    ok = "✓" if score >= 9 else "✗"
    print(f"{label:<38} {score:>6.1f} {ok:>5}  {note}")
